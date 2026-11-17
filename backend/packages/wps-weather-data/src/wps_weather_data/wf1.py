"""The `wf1` dataset: every station observation and forecaster's noon forecast fetched from WF1, as
a Delta Lake table in object storage.

It is to WF1 what `runs` is to the models: an append-only record that `by_time` is built from. A
row is appended only when it is new or differs from the newest version already stored, so a
corrected observation, or a forecast changed between fetches, is a second row with a later
`ingested_at`, and the original stays. That also records forecast history from now on, which WF1
itself does not keep.

The rows have the `by_time` columns. `ACTUALS` rows are hourly observations, `FORECAST` rows are
noon (20:00 UTC) forecasts. A value WF1 does not have, or that is out of range, is null.

The daily observation is not in `wf1`, because WF1 did not supply it: `merge_daily_actuals`
derives it from the hourly observations in `by_time` and writes it there.

Design: docs/architecture/station-weather-storage.md
"""

import logging
import math
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import WriterProperties, write_deltalake
from wps_shared.sfms.raster_addresser import S3Key

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.by_time import (
    ACTUALS,
    BY_TIME_SCHEMA,
    DAILY,
    DAILY_HOUR_UTC,
    FORECAST,
    HOURLY,
    KEY_COLUMNS,
    VALUE_COLUMNS,
    ByTimeTable,
)
from wps_weather_data.table import DeltaWeatherTable

logger = logging.getLogger(__name__)

PARTITION_COLUMNS = ["source", "resolution", "month"]

# The range a value must be in to be kept, as WF1 validation has it.
_VALID_RANGES = {
    "temperature": (-math.inf, math.inf),
    "relative_humidity": (0, 100),
    "wind_speed": (0, math.inf),
    "wind_direction": (0, 360),
    "precipitation": (0, math.inf),
}


def _valid(value, column: str) -> float | None:
    """The value if it is a number in the column's range, else None."""
    if value is None:
        return None
    value = float(value)
    low, high = _VALID_RANGES[column]
    if math.isnan(value) or not low <= value <= high:
        return None
    return value


def _timestamp(value) -> datetime:
    """WF1 records carry their time as an ISO string or a datetime."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.astimezone(UTC)


def _wf1_table(
    records: Iterable, source: str, resolution: str, ingested_at: datetime | None
) -> pa.Table:
    columns: dict[str, list] = {name: [] for name in BY_TIME_SCHEMA.names}
    for record in records:
        timestamp = _timestamp(record.weather_date)
        columns["resolution"].append(resolution)
        columns["source"].append(source)
        columns["month"].append(timestamp.strftime("%Y-%m"))
        columns["station_code"].append(record.station_code)
        columns["timestamp"].append(timestamp)
        for column in _VALID_RANGES:
            columns[column].append(_valid(getattr(record, column), column))
        for column in VALUE_COLUMNS:
            if column not in _VALID_RANGES:
                columns[column].append(None)
        columns["run_ts"].append(None)
        columns["ingested_at"].append(ingested_at or _timestamp(record.created_at))
    return pa.table(columns, schema=BY_TIME_SCHEMA)


def actuals_table(hourly_actuals: Iterable, ingested_at: datetime | None = None) -> pa.Table:
    """Hourly observations (`HourlyActual`s from wps_wf1) as `ACTUALS` rows, fetched at
    `ingested_at`, or each at its own `created_at` when copying history."""
    return _wf1_table(hourly_actuals, ACTUALS, HOURLY, ingested_at)


def forecasts_table(noon_forecasts: Iterable, ingested_at: datetime | None = None) -> pa.Table:
    """Forecasters' noon forecasts (`NoonForecast`s from wps_wf1) as daily `FORECAST` rows,
    fetched at `ingested_at`, or each at its own `created_at` when copying history. The
    precipitation is the forecast 24 hour total."""
    return _wf1_table(noon_forecasts, FORECAST, DAILY, ingested_at)


_DAY = timedelta(hours=24)
_NOON_VALUE_COLUMNS = ("temperature", "relative_humidity", "wind_speed", "wind_direction")


def daily_actuals_table(hourly: pa.Table, since: datetime) -> pa.Table:
    """Daily `ACTUALS` rows from hourly ones: one per station for each 20:00 UTC observation at
    or after `since`.

    The weather values are the 20:00 UTC observation's. The precipitation is the total of the 24
    hours ending then, as in the daily model and forecast rows. It is null unless all 24 hours
    have a value, rather than a total that is too low, so `hourly` must reach 23 hours before
    `since`. The row's `ingested_at` is the newest of the hours it was built from.
    """
    by_station: dict[int, dict[datetime, dict]] = defaultdict(dict)
    for row in hourly.to_pylist():
        by_station[row["station_code"]][row["timestamp"]] = row

    columns: dict[str, list] = {name: [] for name in BY_TIME_SCHEMA.names}
    for station_code, hours in by_station.items():
        for timestamp, noon in hours.items():
            if timestamp < since or (timestamp.hour, timestamp.minute) != (DAILY_HOUR_UTC, 0):
                continue
            day = [hours.get(timestamp - timedelta(hours=back)) for back in range(24)]
            precip = [hour["precipitation"] if hour else None for hour in day]
            columns["resolution"].append(DAILY)
            columns["source"].append(ACTUALS)
            columns["month"].append(timestamp.strftime("%Y-%m"))
            columns["station_code"].append(station_code)
            columns["timestamp"].append(timestamp)
            for column in VALUE_COLUMNS:
                columns[column].append(noon[column] if column in _NOON_VALUE_COLUMNS else None)
            columns["precipitation"][-1] = None if None in precip else sum(precip)
            columns["run_ts"].append(None)
            columns["ingested_at"].append(max(hour["ingested_at"] for hour in day if hour))
    return pa.table(columns, schema=BY_TIME_SCHEMA)


def merge_daily_actuals(by_time: ByTimeTable, hourly_rows: pa.Table) -> int:
    """Write the daily observations that the hourly `ACTUALS` rows just merged into `by_time`
    complete or change. Returns the number of daily rows merged.

    A daily row needs the 24 hours before it, which one fetch does not hold, so the hours are
    read back from `by_time`. Every 20:00 UTC observation from the first of `hourly_rows` to a
    day after the last is rebuilt, so a late or corrected hour updates the day's total.
    """
    if hourly_rows.num_rows == 0:
        return 0
    first = pc.min(hourly_rows["timestamp"]).as_py()
    last = pc.max(hourly_rows["timestamp"]).as_py()
    stored = by_time.read(
        HOURLY,
        [ACTUALS],
        first - _DAY,
        last + _DAY,
        station_codes=pc.unique(hourly_rows["station_code"]).to_pylist(),
    )
    return by_time.merge_wf1_rows(daily_actuals_table(stored, first))


class Wf1Table(DeltaWeatherTable):
    """The `wf1` Delta table."""

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_wf1_key()

    def _newest_stored(self, rows: pa.Table) -> dict[tuple, tuple]:
        """The newest stored values of each of the rows' keys."""
        if not self.exists():
            return {}
        wanted = (
            pc.field("source").isin(pc.unique(rows["source"]).to_pylist())
            & pc.field("resolution").isin(pc.unique(rows["resolution"]).to_pylist())
            & pc.field("month").isin(pc.unique(rows["month"]).to_pylist())
            & pc.field("station_code").isin(pc.unique(rows["station_code"]).to_pylist())
            & (pc.field("timestamp") >= pc.min(rows["timestamp"]).as_py())
            & (pc.field("timestamp") <= pc.max(rows["timestamp"]).as_py())
        )
        stored = self.dataset().to_table(
            columns=[*KEY_COLUMNS, *VALUE_COLUMNS, "ingested_at"], filter=wanted
        )
        newest: dict[tuple, tuple] = {}
        newest_at: dict[tuple, datetime] = {}
        for row in stored.to_pylist():
            key = tuple(row[column] for column in KEY_COLUMNS)
            if key not in newest_at or row["ingested_at"] > newest_at[key]:
                newest_at[key] = row["ingested_at"]
                newest[key] = tuple(row[column] for column in VALUE_COLUMNS)
        return newest

    def append_changed(self, rows: pa.Table) -> pa.Table:
        """Append, in one commit, the rows that are new or differ from the version before them.
        Returns the rows appended.

        The rows may hold several versions of a station and time, as when copying history. They
        are taken in `ingested_at` order, and each is compared with the newest version stored or
        kept before it.
        """
        if rows.num_rows == 0:
            return rows
        previous = self._newest_stored(rows)
        rows = rows.sort_by([("ingested_at", "ascending")])
        changed = []
        for index, row in enumerate(rows.select([*KEY_COLUMNS, *VALUE_COLUMNS]).to_pylist()):
            key = tuple(row[column] for column in KEY_COLUMNS)
            values = tuple(row[column] for column in VALUE_COLUMNS)
            if previous.get(key) != values:
                changed.append(index)
                previous[key] = values
        appended = rows.take(pa.array(changed, pa.int64()))
        if appended.num_rows:
            write_deltalake(
                self.table_uri,
                appended,
                mode="append",
                partition_by=PARTITION_COLUMNS,
                storage_options=self.storage_options,
                writer_properties=WriterProperties(compression="ZSTD"),
            )
        logger.info(
            "Appended %d of %d WF1 rows to wf1; the rest are unchanged",
            appended.num_rows,
            rows.num_rows,
        )
        return appended
