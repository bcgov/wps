"""The `by_time` dataset: the newest value per station, time and source, as a Delta Lake table in
object storage.

For a model, each run is merged in after it is appended to `runs`, replacing every row the run
predicts. Once a time has passed its row stops changing and holds the last prediction made for
it. The table is derived: a model's rows can be rebuilt from `runs`.

Models merge each run in. The WF1 jobs merge observations (`ACTUALS`) and forecasters' noon
forecasts (`FORECAST`), after appending them to `wf1`.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import DeltaTable, WriterProperties
from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.weather_models import ModelEnum

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.runs import build_run_table
from wps_weather_data.table import DeltaWeatherTable

logger = logging.getLogger(__name__)

HOURLY = "hourly"
DAILY = "daily"
# The sources from WF1. Every other source is a model.
ACTUALS = "ACTUALS"
FORECAST = "FORECAST"
# The daily record is the 20:00 UTC (noon PST) row.
DAILY_HOUR_UTC = 20

# The FWI System indices, as WF1 calculates them. An hourly row has only the hourly FFMC, ISI and
# FWI.
FWI_COLUMNS = ("ffmc", "dmc", "dc", "isi", "bui", "fwi")

# The columns only WF1 and the data mart have values for. A model's rows leave them null.
OBSERVED_COLUMNS = {
    **{column: pa.float32() for column in FWI_COLUMNS},
    "dewpoint": pa.float32(),
    # Data mart hourly observations only: WF1's records do not carry it.
    "wind_gust": pa.float32(),
    # Percent cured, on WF1's dailies and noon forecasts.
    "grass_curing": pa.float32(),
    # WF1's forest danger class, 1 to 5, on daily actuals.
    "danger_rating": pa.int8(),
    # Whether WF1 accepted an actual, and why not. Null for a data mart observation, which does
    # not say.
    "observation_valid": pa.bool_(),
    "observation_valid_comment": pa.string(),
}

# Every value column and its type.
VALUE_TYPES = {
    **{
        column: pa.float32()
        for column in (
            "temperature",
            "relative_humidity",
            "wind_speed",
            "wind_direction",
            "precipitation",
            "bias_adjusted_temperature",
            "bias_adjusted_relative_humidity",
            "bias_adjusted_wind_speed",
            "bias_adjusted_wind_direction",
            "bias_adjusted_precipitation",
        )
    },
    **OBSERVED_COLUMNS,
}

VALUE_COLUMNS = tuple(VALUE_TYPES)

_TIMESTAMP = pa.timestamp("us", tz="UTC")

BY_TIME_SCHEMA = pa.schema(
    [
        ("resolution", pa.string()),
        ("source", pa.string()),
        ("month", pa.string()),
        ("station_code", pa.int32()),
        ("timestamp", _TIMESTAMP),
        *VALUE_TYPES.items(),
        ("run_ts", _TIMESTAMP),
        ("ingested_at", _TIMESTAMP),
    ]
)

PARTITION_COLUMNS = ["resolution", "source", "month"]

# What identifies a row: there is one per station, time, resolution and source.
KEY_COLUMNS = ("source", "resolution", "station_code", "timestamp")

# by_time column -> runs column, for the columns that mean the same at both resolutions.
_FROM_RUN = {
    "temperature": "tmp_tgl_2",
    "relative_humidity": "rh_tgl_2",
    "wind_speed": "wind_tgl_10",
    "wind_direction": "wdir_tgl_10",
    "bias_adjusted_temperature": "bias_adjusted_temperature",
    "bias_adjusted_relative_humidity": "bias_adjusted_rh",
    "bias_adjusted_wind_speed": "bias_adjusted_wind_speed",
    "bias_adjusted_wind_direction": "bias_adjusted_wdir",
}


def _rows_at_resolution(run: pa.Table, resolution: str) -> pa.Table:
    count = run.num_rows
    if resolution == HOURLY:
        # The precipitation since the model's previous prediction. There is no bias-adjusted
        # value for it.
        precipitation = run["delta_precip"]
        bias_adjusted_precipitation = pa.nulls(count, pa.float32())
    else:
        precipitation = run["precip_24h"]
        bias_adjusted_precipitation = run["bias_adjusted_precip_24h"]
    columns = {
        "resolution": pa.array([resolution] * count, pa.string()),
        "source": run["model"],
        "month": pc.strftime(run["prediction_timestamp"], format="%Y-%m"),
        "station_code": run["station_code"],
        "timestamp": run["prediction_timestamp"],
        **{column: run[run_column] for column, run_column in _FROM_RUN.items()},
        "precipitation": precipitation,
        "bias_adjusted_precipitation": bias_adjusted_precipitation,
        **{column: pa.nulls(count, kind) for column, kind in OBSERVED_COLUMNS.items()},
        "run_ts": run["run_ts"],
        "ingested_at": run["ingested_at"],
    }
    return pa.table({name: columns[name] for name in BY_TIME_SCHEMA.names}, schema=BY_TIME_SCHEMA)


def by_time_rows_from_run(run: pa.Table) -> pa.Table:
    """Turn one run's rows, in the `runs` schema, into its hourly and daily `by_time` rows.

    Every prediction becomes an hourly row. The 20:00 UTC predictions also become daily rows,
    carrying the 24-hour precipitation.
    """
    at_daily_hour = pc.equal(pc.hour(run["prediction_timestamp"]), DAILY_HOUR_UTC)
    return pa.concat_tables(
        [_rows_at_resolution(run, HOURLY), _rows_at_resolution(run.filter(at_daily_hour), DAILY)]
    )


def newest_per_key(rows: pa.Table) -> pa.Table:
    """The newest version of each station and time in the rows."""
    if rows.num_rows == 0:
        return rows
    keys = list(KEY_COLUMNS)
    newest = rows.group_by(keys).aggregate([("ingested_at", "max")])
    rows = rows.join(newest, keys=keys)
    rows = rows.filter(pc.equal(rows["ingested_at"], rows["ingested_at_max"]))
    return rows.select(BY_TIME_SCHEMA.names)


class ByTimeTable(DeltaWeatherTable):
    """The `by_time` Delta table."""

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_by_time_key()

    def merge_run(
        self,
        model: ModelEnum,
        run_ts: datetime,
        rows: Iterable[Mapping],
        *,
        ingested_at: datetime | None = None,
    ) -> int:
        """Merge a model run in. Returns the number of rows the run offered.

        A row is replaced only by a run at least as new as the one it came from, so merging an
        older run, as a backfill does, fills gaps without undoing newer predictions.
        """
        run = build_run_table(model, run_ts, rows, ingested_at or datetime.now(UTC))
        source = by_time_rows_from_run(run)
        if source.num_rows == 0:
            logger.warning(
                "No rows for %s run %s, nothing merged into by_time", model.value, run_ts
            )
            return 0

        self._merge(source, newer="s.run_ts >= t.run_ts")
        logger.info(
            "Merged %s rows for %s run %s into by_time", source.num_rows, model.value, run_ts
        )
        return source.num_rows

    def merge_wf1_rows(self, rows: pa.Table) -> int:
        """Merge rows from WF1 (`ACTUALS` or `FORECAST`), in the `by_time` schema. Returns the
        number of rows merged.

        A row is replaced only by one fetched at least as recently, so a backfill of older
        fetches does not undo newer values.
        """
        if rows.num_rows == 0:
            return 0
        # A merge takes one row per station and time, so only the newest version of each.
        rows = newest_per_key(rows)
        self._merge(rows, newer="s.ingested_at >= t.ingested_at")
        logger.info("Merged %s WF1 rows into by_time", rows.num_rows)
        return rows.num_rows

    def _merge(self, source: pa.Table, *, newer: str):
        """Merge rows in on station, time, resolution and source. A matched row is replaced
        when `newer` holds."""
        table = DeltaTable.create(
            self.table_uri,
            schema=BY_TIME_SCHEMA,
            partition_by=PARTITION_COLUMNS,
            mode="ignore",
            storage_options=self.storage_options,
        )
        # Naming the sources and months as literals lets the merge skip every other partition.
        sources = ", ".join(f"'{name}'" for name in sorted(set(source["source"].to_pylist())))
        months = ", ".join(f"'{month}'" for month in sorted(set(source["month"].to_pylist())))
        predicate = (
            f"t.source IN ({sources}) AND t.month IN ({months}) "
            "AND t.resolution = s.resolution AND t.source = s.source AND t.month = s.month "
            'AND t.station_code = s.station_code AND t."timestamp" = s."timestamp"'
        )
        (
            table.merge(
                source,
                predicate,
                source_alias="s",
                target_alias="t",
                writer_properties=WriterProperties(compression="ZSTD"),
            )
            .when_matched_update_all(predicate=newer)
            .when_not_matched_insert_all()
            .execute()
        )

    def read(
        self,
        resolution: str,
        sources: Sequence[str],
        start: datetime,
        end: datetime,
        *,
        station_codes: Sequence[int] | None = None,
    ) -> pa.Table:
        """Read the rows for the given sources with a timestamp in [start, end].

        Returns an empty table if the `by_time` table does not exist yet.
        """
        if not self.exists():
            return BY_TIME_SCHEMA.empty_table()

        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        wanted = (
            (pc.field("resolution") == resolution)
            & pc.field("source").isin(list(sources))
            & (pc.field("month") >= start.strftime("%Y-%m"))
            & (pc.field("month") <= end.strftime("%Y-%m"))
            & (pc.field("timestamp") >= start)
            & (pc.field("timestamp") <= end)
        )
        if station_codes is not None:
            wanted = wanted & pc.field("station_code").isin(list(station_codes))
        dataset = self.dataset()
        return (
            dataset.to_table(filter=wanted)
            .select(BY_TIME_SCHEMA.names)
            .sort_by(
                [("source", "ascending"), ("station_code", "ascending"), ("timestamp", "ascending")]
            )
        )
