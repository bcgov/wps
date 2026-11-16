"""The `runs` dataset: station values from every weather model run, as a Delta Lake table in
object storage.

A run is appended in one commit. A reprocessed run is appended again with a later `ingested_at`,
and readers take the newest version of each run. Every reader should go through `read_runs` so
that rule lives in one place.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import DeltaTable, WriterProperties, write_deltalake
from wps_shared.weather_models import ModelEnum

from wps_weather_data.store import resolve_table

logger = logging.getLogger(__name__)

RUNS_KEY = "weather/stations/runs"

VALUE_COLUMNS = (
    "tmp_tgl_2",
    "rh_tgl_2",
    "apcp_sfc_0",
    "wdir_tgl_10",
    "wind_tgl_10",
    "bias_adjusted_temperature",
    "bias_adjusted_rh",
    "bias_adjusted_wdir",
    "bias_adjusted_wind_speed",
    "delta_precip",
    "precip_24h",
    "bias_adjusted_precip_24h",
)

_TIMESTAMP = pa.timestamp("us", tz="UTC")

RUNS_SCHEMA = pa.schema(
    [
        ("model", pa.string()),
        ("run_date", pa.date32()),
        ("station_code", pa.int32()),
        ("run_ts", _TIMESTAMP),
        ("prediction_timestamp", _TIMESTAMP),
        *[(column, pa.float32()) for column in VALUE_COLUMNS],
        ("ingested_at", _TIMESTAMP),
        # Null when it is no longer known whether the job interpolated the row.
        ("is_interpolated", pa.bool_()),
    ]
)

PARTITION_COLUMNS = ["model", "run_date"]


def build_run_table(
    model: ModelEnum, run_ts: datetime, rows: Iterable[Mapping], ingested_at: datetime
) -> pa.Table:
    """Build one run's rows in the `runs` schema, sorted by station then prediction time.

    Each row needs `station_code` and `prediction_timestamp`. Value columns and
    `is_interpolated` are null when missing.
    """
    rows = list(rows)
    count = len(rows)
    columns = {
        "model": [model.value] * count,
        "run_date": [run_ts.astimezone(UTC).date()] * count,
        "station_code": [row["station_code"] for row in rows],
        "run_ts": [run_ts] * count,
        "prediction_timestamp": [row["prediction_timestamp"] for row in rows],
        **{column: [row.get(column) for row in rows] for column in VALUE_COLUMNS},
        "ingested_at": [ingested_at] * count,
        "is_interpolated": [row.get("is_interpolated") for row in rows],
    }
    table = pa.table(columns, schema=RUNS_SCHEMA)
    return table.sort_by([("station_code", "ascending"), ("prediction_timestamp", "ascending")])


def append_run(
    model: ModelEnum,
    run_ts: datetime,
    rows: Iterable[Mapping],
    *,
    ingested_at: datetime | None = None,
    table_uri: str | None = None,
    storage_options: dict[str, str] | None = None,
) -> int:
    """Append one version of a model run to `runs` in a single commit. Returns the rows written.

    `table_uri` and `storage_options` default to our object store.
    """
    table_uri, storage_options = resolve_table(RUNS_KEY, table_uri, storage_options)
    table = build_run_table(model, run_ts, rows, ingested_at or datetime.now(UTC))
    if table.num_rows == 0:
        logger.warning("No rows for %s run %s, nothing appended to runs", model.value, run_ts)
        return 0
    write_deltalake(
        table_uri,
        table,
        mode="append",
        partition_by=PARTITION_COLUMNS,
        storage_options=storage_options,
        writer_properties=WriterProperties(compression="ZSTD"),
    )
    logger.info("Appended %s rows for %s run %s to runs", table.num_rows, model.value, run_ts)
    return table.num_rows


def read_runs(
    model: ModelEnum,
    run_from: datetime,
    run_to: datetime,
    *,
    station_codes: Sequence[int] | None = None,
    table_uri: str | None = None,
    storage_options: dict[str, str] | None = None,
) -> pa.Table:
    """Read the newest version of each of a model's runs that started in [run_from, run_to].

    Returns an empty table if the `runs` table does not exist yet.
    """
    table_uri, storage_options = resolve_table(RUNS_KEY, table_uri, storage_options)
    if not DeltaTable.is_deltatable(table_uri, storage_options=storage_options):
        return RUNS_SCHEMA.empty_table()

    run_from = run_from.astimezone(UTC)
    run_to = run_to.astimezone(UTC)
    dataset = DeltaTable(table_uri, storage_options=storage_options).to_pyarrow_dataset()
    in_range = (
        (pc.field("model") == model.value)
        & (pc.field("run_date") >= run_from.date())
        & (pc.field("run_date") <= run_to.date())
        & (pc.field("run_ts") >= run_from)
        & (pc.field("run_ts") <= run_to)
    )

    # The newest version is chosen per run, before any station filter. Choosing it per row would
    # bring back a station that an older version had and the newest version dropped.
    newest = (
        dataset.to_table(columns=["run_ts", "ingested_at"], filter=in_range)
        .group_by("run_ts")
        .aggregate([("ingested_at", "max")])
    )
    wanted = in_range
    if station_codes is not None:
        wanted = wanted & pc.field("station_code").isin(list(station_codes))
    rows = dataset.to_table(filter=wanted).join(newest, keys="run_ts")
    rows = rows.filter(pc.equal(rows["ingested_at"], rows["ingested_at_max"]))
    return rows.select(RUNS_SCHEMA.names).sort_by(
        [
            ("run_ts", "ascending"),
            ("station_code", "ascending"),
            ("prediction_timestamp", "ascending"),
        ]
    )
