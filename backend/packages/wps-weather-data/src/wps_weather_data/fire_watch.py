"""Fire watch's model values, read from the `runs` table.

Every 20:00 UTC prediction of one run for some stations. Fire watch works from a single run, not
the newest value per day, so it reads `runs` rather than `by_time`.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from time import perf_counter

import pyarrow.compute as pc
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.weather_models import ModelEnum

from wps_weather_data.runs import RunsTable

logger = logging.getLogger(__name__)

DAILY_HOUR_UTC = 20


def fetch_daily_run_predictions(
    runs: RunsTable,
    model: ModelEnum,
    run_ts: datetime,
    station_codes: Sequence[int],
) -> list[ModelPredictionDetails]:
    """Get one run's 20:00 UTC predictions for the stations, by station then prediction time."""
    started = perf_counter()
    rows = runs.read(model, run_ts, run_ts, station_codes=station_codes)
    rows = rows.filter(pc.equal(pc.hour(rows["prediction_timestamp"]), DAILY_HOUR_UTC))
    predictions = [
        ModelPredictionDetails(
            prediction_timestamp=row["prediction_timestamp"],
            # When the run was written to `runs`, standing in for the Postgres row's update date.
            update_date=row["ingested_at"],
            abbreviation=row["model"],
            prediction_run_timestamp=row["run_ts"],
            station_code=row["station_code"],
            rh_tgl_2=row["rh_tgl_2"],
            tmp_tgl_2=row["tmp_tgl_2"],
            bias_adjusted_temperature=row["bias_adjusted_temperature"],
            bias_adjusted_rh=row["bias_adjusted_rh"],
            bias_adjusted_wind_speed=row["bias_adjusted_wind_speed"],
            bias_adjusted_wdir=row["bias_adjusted_wdir"],
            precip_24h=row["precip_24h"],
            bias_adjusted_precip_24h=row["bias_adjusted_precip_24h"],
            wdir_tgl_10=row["wdir_tgl_10"],
            wind_tgl_10=row["wind_tgl_10"],
        )
        for row in rows.sort_by(
            [("station_code", "ascending"), ("prediction_timestamp", "ascending")]
        ).to_pylist()
    ]
    logger.info(
        "Read %d %s predictions from run %s for %d stations in %.3f s",
        len(predictions),
        model.value,
        run_ts,
        len(station_codes),
        perf_counter() - started,
    )
    return predictions
