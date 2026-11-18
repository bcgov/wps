"""The `wf1` dataset: every station observation and forecaster's noon forecast fetched from WF1, as
a Delta Lake table in object storage.

It is to WF1 what `runs` is to the models: an append-only record that `by_time` is built from. A
row is appended only when it is new or differs from the newest version already stored, so a
corrected observation, or a forecast changed between fetches, is a second row with a later
`ingested_at`, and the original stays. That also records forecast history from now on, which WF1
itself does not keep.

The rows have the `by_time` columns. `ACTUALS` rows are hourly observations and WF1's daily
actuals, `FORECAST` rows are noon (20:00 UTC) forecasts. Each carries the FWI System indices WF1
calculated for it, and an actual whether WF1 accepted it. A value WF1 does not have, or that is
out of range, is null.

A daily actual is WF1's own daily record for 20:00 UTC. Its precipitation is the total WF1
accumulated over the 24 hours before, so nothing here adds up hourly values.

Design: docs/architecture/station-weather-storage.md
"""

import logging
import math
from collections.abc import Iterable
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import WriterProperties, write_deltalake
from wps_shared.sfms.raster_addresser import S3Key

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.by_time import (
    ACTUALS,
    BY_TIME_SCHEMA,
    DAILY,
    FORECAST,
    HOURLY,
    KEY_COLUMNS,
    VALUE_COLUMNS,
)
from wps_weather_data.table import DeltaWeatherTable

logger = logging.getLogger(__name__)

PARTITION_COLUMNS = ["source", "resolution", "month"]

# The range a value must be in to be kept, as WF1 validation has it.
VALID_RANGES = {
    "temperature": (-math.inf, math.inf),
    "relative_humidity": (0, 100),
    "wind_speed": (0, math.inf),
    "wind_direction": (0, 360),
    "precipitation": (0, math.inf),
    "ffmc": (0, 101),
    "dmc": (0, math.inf),
    "dc": (0, math.inf),
    "isi": (0, math.inf),
    "bui": (0, math.inf),
    "fwi": (0, math.inf),
    "dewpoint": (-math.inf, math.inf),
    "wind_gust": (0, math.inf),
    "grass_curing": (0, 100),
    "danger_rating": (1, 5),
}

# by_time column -> the record attribute it is read from, where they differ: a noon forecast
# calls grass curing `gc`.
_ATTRIBUTES = {"grass_curing": ("grass_curing", "gc")}


def _valid(value, column: str) -> float | None:
    """The value if it is a number in the column's range, else None."""
    if value is None:
        return None
    value = float(value)
    low, high = VALID_RANGES[column]
    if math.isnan(value) or not low <= value <= high:
        return None
    return value


def _attribute(record, column: str):
    """The record's value for a by_time column, or None if this kind of record has none."""
    for name in _ATTRIBUTES.get(column, (column,)):
        value = getattr(record, name, None)
        if value is not None:
            return value
    return None


def _timestamp(value) -> datetime:
    """WF1 records carry their time as an ISO string or a datetime."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.astimezone(UTC)


def _wf1_table(
    records: Iterable,
    source: str,
    resolution: str,
    ingested_at: datetime | None,
    *,
    station_code: str = "station_code",
    time: str = "weather_date",
) -> pa.Table:
    """Rows from WF1 records. `station_code` and `time` name the records' attributes."""
    columns: dict[str, list] = {name: [] for name in BY_TIME_SCHEMA.names}
    for record in records:
        timestamp = _timestamp(getattr(record, time))
        columns["resolution"].append(resolution)
        columns["source"].append(source)
        columns["month"].append(timestamp.strftime("%Y-%m"))
        columns["station_code"].append(getattr(record, station_code))
        columns["timestamp"].append(timestamp)
        for column in VALUE_COLUMNS:
            if column in VALID_RANGES:
                # Not every kind of record has every value: an hourly one has no DMC, DC or BUI.
                columns[column].append(_valid(_attribute(record, column), column))
            elif column in ("observation_valid", "observation_valid_comment"):
                columns[column].append(_attribute(record, column))
            else:
                columns[column].append(None)
        columns["run_ts"].append(None)
        columns["ingested_at"].append(ingested_at or _timestamp(record.created_at))
    return pa.table(columns, schema=BY_TIME_SCHEMA)


def actuals_table(hourly_actuals: Iterable, ingested_at: datetime | None = None) -> pa.Table:
    """Hourly observations (`HourlyActual`s from wps_wf1) as `ACTUALS` rows, fetched at
    `ingested_at`, or each at its own `created_at` when copying history."""
    return _wf1_table(hourly_actuals, ACTUALS, HOURLY, ingested_at)


def daily_actuals_table(dailies: Iterable, ingested_at: datetime) -> pa.Table:
    """WF1's daily actuals (`SFMSDaily`s from wps_wf1) as daily `ACTUALS` rows, fetched at
    `ingested_at`. The precipitation is WF1's 24 hour total."""
    return _wf1_table(
        dailies, ACTUALS, DAILY, ingested_at, station_code="code", time="for_datetime"
    )


def forecasts_table(noon_forecasts: Iterable, ingested_at: datetime | None = None) -> pa.Table:
    """Forecasters' noon forecasts (`NoonForecast`s from wps_wf1) as daily `FORECAST` rows,
    fetched at `ingested_at`, or each at its own `created_at` when copying history. The
    precipitation is the forecast 24 hour total."""
    return _wf1_table(noon_forecasts, FORECAST, DAILY, ingested_at)


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
