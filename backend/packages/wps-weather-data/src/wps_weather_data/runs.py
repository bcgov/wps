"""The `runs` dataset: station values from every weather model run, as a Delta Lake table in
object storage.

A run is appended in one commit. A reprocessed run is appended again with a later `ingested_at`,
and readers take the newest version of each run. Every reader should go through
`RunsTable.read` so that rule lives in one place.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import WriterProperties, write_deltalake
from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.weather_models import ModelEnum

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.table import TABLE_CONFIGURATION, DeltaWeatherTable

logger = logging.getLogger(__name__)

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


class RunsTable(DeltaWeatherTable):
    """The `runs` Delta table."""

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_runs_key()

    def append_run(
        self,
        model: ModelEnum,
        run_ts: datetime,
        rows: Iterable[Mapping],
        *,
        ingested_at: datetime | None = None,
    ) -> int:
        """Append one version of a model run in a single commit. Returns the rows written."""
        table = build_run_table(model, run_ts, rows, ingested_at or datetime.now(UTC))
        if table.num_rows == 0:
            logger.warning("No rows for %s run %s, nothing appended to runs", model.value, run_ts)
            return 0
        write_deltalake(
            self.table_uri,
            table,
            mode="append",
            partition_by=PARTITION_COLUMNS,
            storage_options=self.storage_options,
            configuration=TABLE_CONFIGURATION,
            writer_properties=WriterProperties(compression="ZSTD"),
        )
        logger.info("Appended %s rows for %s run %s to runs", table.num_rows, model.value, run_ts)
        return table.num_rows

    def _runs_filter(self, model: ModelEnum, run_from: datetime, run_to: datetime):
        run_from = run_from.astimezone(UTC)
        run_to = run_to.astimezone(UTC)
        return (
            (pc.field("model") == model.value)
            & (pc.field("run_date") >= run_from.date())
            & (pc.field("run_date") <= run_to.date())
            & (pc.field("run_ts") >= run_from)
            & (pc.field("run_ts") <= run_to)
        )

    def has_run(self, model: ModelEnum, run_ts: datetime) -> bool:
        """Whether the run has been published."""
        if not self.exists():
            return False
        return self.dataset().count_rows(filter=self._runs_filter(model, run_ts, run_ts)) > 0

    def latest_run_ts(self, model: ModelEnum, since: datetime) -> datetime | None:
        """The newest published run of the model that started at or after `since`, if any."""
        if not self.exists():
            return None
        run_timestamps = self.dataset().to_table(
            columns=["run_ts"], filter=self._runs_filter(model, since, datetime.now(UTC))
        )["run_ts"]
        return pc.max(run_timestamps).as_py()

    def read(
        self,
        model: ModelEnum,
        run_from: datetime,
        run_to: datetime,
        *,
        station_codes: Sequence[int] | None = None,
        predicted_from: datetime | None = None,
        predicted_to: datetime | None = None,
        columns: Sequence[str] | None = None,
    ) -> pa.Table:
        """Read the newest version of each of a model's runs that started in [run_from, run_to].

        `predicted_from` and `predicted_to` keep the predictions for times in that range, and
        `columns` keeps only those columns, which matters when reading many runs.

        Returns an empty table if the `runs` table does not exist yet.
        """
        columns = list(RUNS_SCHEMA.names if columns is None else columns)
        if not self.exists():
            return RUNS_SCHEMA.empty_table().select(columns)

        dataset = self.dataset()
        in_range = self._runs_filter(model, run_from, run_to)

        # The newest version is chosen per run, before any other filter. Choosing it per row would
        # bring back a station that an older version had and the newest version dropped.
        newest = (
            dataset.to_table(columns=["run_ts", "ingested_at"], filter=in_range)
            .group_by("run_ts")
            .aggregate([("ingested_at", "max")])
        )
        wanted = in_range
        if station_codes is not None:
            wanted = wanted & pc.field("station_code").isin(list(station_codes))
        if predicted_from is not None:
            wanted = wanted & (pc.field("prediction_timestamp") >= predicted_from.astimezone(UTC))
        if predicted_to is not None:
            wanted = wanted & (pc.field("prediction_timestamp") <= predicted_to.astimezone(UTC))
        read_columns = list(dict.fromkeys([*columns, "run_ts", "ingested_at"]))
        rows = dataset.to_table(columns=read_columns, filter=wanted).join(newest, keys="run_ts")
        rows = rows.filter(pc.equal(rows["ingested_at"], rows["ingested_at_max"]))
        order = [
            (name, "ascending")
            for name in ("run_ts", "station_code", "prediction_timestamp")
            if name in columns
        ]
        rows = rows.select(columns)
        return rows.sort_by(order) if order else rows
