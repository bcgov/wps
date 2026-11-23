"""The `staging` dataset: a model's station values from runs that are still downloading, as a
Delta Lake table in object storage.

A run arrives as hundreds of GRIB files published over hours, and a job invocation processes
whatever is available, then exits. The values it extracted are kept here until every file of the
run has been processed. The job then reads the run back, computes the station predictions, appends
them to `runs`, merges them into `by_time` and deletes the run from here.

Each model has its own table, so each table has a single writer: the model's job.

Every processed file leaves one marker row, written in the same commit as its values. The files a
run has processed are the distinct `source` values of its rows, so a file is either processed with
all of its values or not at all.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import WriterProperties, write_deltalake
from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.weather_models import ModelEnum

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.table import TABLE_CONFIGURATION, DeltaWeatherTable

logger = logging.getLogger(__name__)

# The model fields a station value can be. Others in a GRIB file are not kept.
MODEL_FIELDS = ("tmp_tgl_2", "rh_tgl_2", "apcp_sfc_0", "wdir_tgl_10", "wind_tgl_10")

_TIMESTAMP = pa.timestamp("us", tz="UTC")

STAGING_SCHEMA = pa.schema(
    [
        # The run, as a partition value such as 20261117T00.
        ("run", pa.string()),
        ("run_ts", _TIMESTAMP),
        # Null on a file's marker row.
        ("station_code", pa.int32()),
        ("prediction_timestamp", _TIMESTAMP),
        # Null on a file's marker row.
        ("variable", pa.string()),
        # Kept at full precision: the station predictions are computed from it.
        ("value", pa.float64()),
        # The file the row came from, such as its URL.
        ("source", pa.string()),
        ("written_at", _TIMESTAMP),
    ]
)

PARTITION_COLUMNS = ["run"]


def run_partition(run_ts: datetime) -> str:
    """The partition value of a run."""
    return run_ts.astimezone(UTC).strftime("%Y%m%dT%H")


@dataclass
class StagedFile:
    """The station values extracted from one processed file."""

    source: str
    prediction_timestamp: datetime
    # (station_code, prediction_timestamp, variable, value)
    values: list[tuple[int, datetime, str, float | None]] = field(default_factory=list)


class StagingTable(DeltaWeatherTable):
    """A model's `staging` Delta table."""

    def __init__(
        self,
        model: ModelEnum,
        table_uri: str | None = None,
        storage_options: dict[str, str] | None = None,
    ):
        self.model = model
        super().__init__(table_uri, storage_options)

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_staging_key(self.model.value)

    def append_files(self, run_ts: datetime, files: Iterable[StagedFile]) -> int:
        """Record processed files and their values for a run, in one commit. Returns the files
        recorded."""
        files = list(files)
        if not files:
            return 0
        written_at = datetime.now(UTC)
        run = run_partition(run_ts)
        columns: dict[str, list] = {name: [] for name in STAGING_SCHEMA.names}

        def add(station_code, prediction_timestamp, variable, value, source):
            columns["run"].append(run)
            columns["run_ts"].append(run_ts)
            columns["station_code"].append(station_code)
            columns["prediction_timestamp"].append(prediction_timestamp)
            columns["variable"].append(variable)
            columns["value"].append(value)
            columns["source"].append(source)
            columns["written_at"].append(written_at)

        for staged in files:
            add(None, staged.prediction_timestamp, None, None, staged.source)
            for station_code, prediction_timestamp, variable, value in staged.values:
                add(station_code, prediction_timestamp, variable, value, staged.source)

        write_deltalake(
            self.table_uri,
            pa.table(columns, schema=STAGING_SCHEMA),
            mode="append",
            partition_by=PARTITION_COLUMNS,
            storage_options=self.storage_options,
            configuration=TABLE_CONFIGURATION,
            writer_properties=WriterProperties(compression="ZSTD"),
        )
        logger.info(
            "Staged %d files for %s run %s", len(files), self.model.value, run_ts.isoformat()
        )
        return len(files)

    def _run_filter(self, run_ts: datetime) -> pc.Expression:
        return pc.field("run") == run_partition(run_ts)

    def has_run(self, run_ts: datetime) -> bool:
        """Whether any file of the run has been staged."""
        if not self.exists():
            return False
        return self.dataset().count_rows(filter=self._run_filter(run_ts)) > 0

    def last_written_at(self, run_ts: datetime) -> datetime | None:
        """When a file of the run was last staged, if any has been."""
        if not self.exists():
            return None
        written_at = self.dataset().to_table(
            columns=["written_at"], filter=self._run_filter(run_ts)
        )["written_at"]
        return pc.max(written_at).as_py()

    def processed_sources(self, run_ts: datetime) -> set[str]:
        """The files of the run that have been processed."""
        if not self.exists():
            return set()
        sources = self.dataset().to_table(columns=["source"], filter=self._run_filter(run_ts))
        return set(pc.unique(sources["source"]).to_pylist())

    def station_values(self, run_ts: datetime) -> dict[int, list[dict]]:
        """The run's values per station: one dict per prediction time, in time order, with a key
        for each of MODEL_FIELDS (None when missing) and `prediction_timestamp`.

        A value staged more than once, as when a file is processed again, takes the newest.
        """
        if not self.exists():
            return {}
        rows = self.dataset().to_table(
            columns=["station_code", "prediction_timestamp", "variable", "value", "written_at"],
            filter=self._run_filter(run_ts)
            & pc.field("variable").isin(list(MODEL_FIELDS))
            & pc.field("station_code").is_valid(),
        )
        newest = (
            rows.sort_by([("written_at", "ascending")])
            .group_by(["station_code", "prediction_timestamp", "variable"], use_threads=False)
            .aggregate([("value", "last")])
        )
        by_station: dict[int, dict[datetime, dict]] = defaultdict(dict)
        for station_code, prediction_timestamp, variable, value in zip(
            newest["station_code"].to_pylist(),
            newest["prediction_timestamp"].to_pylist(),
            newest["variable"].to_pylist(),
            newest["value_last"].to_pylist(),
        ):
            values = by_station[station_code].get(prediction_timestamp)
            if values is None:
                values = {"prediction_timestamp": prediction_timestamp}
                values.update(dict.fromkeys(MODEL_FIELDS))
                by_station[station_code][prediction_timestamp] = values
            values[variable] = value
        return {
            station_code: [times[time] for time in sorted(times)]
            for station_code, times in by_station.items()
        }

    def delete_run(self, run_ts: datetime):
        """Delete the run, once it is published to `runs` and `by_time`."""
        if not self.exists():
            return
        self.open().delete(f"run = '{run_partition(run_ts)}'")
        logger.info("Deleted %s run %s from staging", self.model.value, run_ts.isoformat())
