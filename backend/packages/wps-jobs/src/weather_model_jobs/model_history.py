"""A model's recent station predictions, read from `runs` to train the bias adjustments.

Read once per model run being processed and shared by every station's training, so the job makes
one read of `runs` per run rather than one per station.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
from wps_shared.weather_models import ModelEnum
from wps_weather_data.runs import RunsTable

from weather_model_jobs.model_values import ModelValues

logger = logging.getLogger(__name__)

# The longest lead time of any model (GFS, 264 hours). A run older than this predicts nothing in a
# window, so reading the runs that started up to this long before the window finds them all.
LEAD_MARGIN = timedelta(days=11)

DAILY_HOUR_UTC = 20

_HOURLY_COLUMNS = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10", "wdir_tgl_10")


@dataclass(frozen=True)
class DailyPrecip:
    """One run's 24 hour precip prediction for a day, ending at 20:00 UTC."""

    prediction_timestamp: datetime
    precip_24h: float | None


def _model_own_values(rows: pa.Table) -> pa.Table:
    """The rows holding the model's own values, not ones the job interpolated.

    A row of a run backfilled after its model values were deleted does not know whether it was
    interpolated. Only a 20:00 UTC row ever is, so such rows count as the model's own except at
    20:00, where they are left out.
    """
    interpolated = rows["is_interpolated"]
    own = pc.or_kleene(
        pc.equal(interpolated, False),
        pc.and_kleene(
            pc.is_null(interpolated),
            pc.not_equal(pc.hour(rows["prediction_timestamp"]), DAILY_HOUR_UTC),
        ),
    )
    return rows.filter(pc.fill_null(own, False))


def _newest_run_per_time(rows: pa.Table) -> pa.Table:
    """For each station and time, the row from the newest run that predicted it."""
    newest = rows.group_by(["station_code", "prediction_timestamp"]).aggregate([("run_ts", "max")])
    rows = rows.join(newest, keys=["station_code", "prediction_timestamp"])
    return rows.filter(pc.equal(rows["run_ts"], rows["run_ts_max"]))


class ModelHistory:
    """For each station, the model's newest own value per time, to pair with observations, and
    every run's 24 hour precip per day."""

    def __init__(
        self,
        newest_values: dict[int, dict[datetime, ModelValues]],
        daily_precip: dict[int, list[DailyPrecip]],
    ):
        self._newest_values = newest_values
        self._daily_precip = daily_precip

    @classmethod
    def read(
        cls,
        runs: RunsTable,
        model: ModelEnum,
        hourly_from: datetime,
        hourly_to: datetime,
        daily_from: datetime,
        daily_to: datetime,
    ) -> "ModelHistory":
        """Read the model's values for times in [hourly_from, hourly_to], and its 20:00 UTC
        predictions for times in [daily_from, daily_to)."""
        earliest = min(hourly_from, daily_from)
        rows = runs.read(
            model,
            earliest - LEAD_MARGIN,
            max(hourly_to, daily_to),
            predicted_from=earliest,
            predicted_to=max(hourly_to, daily_to),
            columns=[
                "station_code",
                "prediction_timestamp",
                "run_ts",
                *_HOURLY_COLUMNS,
                "precip_24h",
                "is_interpolated",
            ],
        )
        times = rows["prediction_timestamp"]

        hourly = rows.filter(
            pc.and_(pc.greater_equal(times, hourly_from), pc.less_equal(times, hourly_to))
        )
        hourly = _newest_run_per_time(_model_own_values(hourly))
        newest_values: dict[int, dict[datetime, ModelValues]] = defaultdict(dict)
        for row in hourly.select(
            ["station_code", "prediction_timestamp", *_HOURLY_COLUMNS]
        ).to_pylist():
            newest_values[row["station_code"]][row["prediction_timestamp"]] = ModelValues(**row)

        daily = rows.filter(
            pc.and_(
                pc.and_(pc.greater_equal(times, daily_from), pc.less(times, daily_to)),
                pc.equal(pc.hour(times), DAILY_HOUR_UTC),
            )
        )
        daily_precip: dict[int, list[DailyPrecip]] = defaultdict(list)
        for row in daily.select(["station_code", "prediction_timestamp", "precip_24h"]).to_pylist():
            daily_precip[row["station_code"]].append(
                DailyPrecip(row["prediction_timestamp"], row["precip_24h"])
            )

        logger.info(
            "Read %s history from runs: %d hourly values and %d daily precip predictions",
            model.value,
            hourly.num_rows,
            daily.num_rows,
        )
        return cls(dict(newest_values), dict(daily_precip))

    def newest_value(self, station_code: int, time: datetime) -> ModelValues | None:
        """The newest run's own values for the station at the time, if any run predicted it."""
        return self._newest_values.get(station_code, {}).get(time)

    def daily_precip(self, station_code: int, start: datetime, end: datetime) -> list[DailyPrecip]:
        """Every run's 24 hour precip prediction for the station at times in [start, end)."""
        return [
            precip
            for precip in self._daily_precip.get(station_code, [])
            if start <= precip.prediction_timestamp < end
        ]
