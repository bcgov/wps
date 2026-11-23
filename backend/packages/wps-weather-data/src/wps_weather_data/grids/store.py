"""A model's grid store: `recent`, every run for about the last day, or `history`, one run a day.

Each is an Icechunk repository with a group per run, named by its start time (`2026-11-19T18`).
A group has an array per variable of GRIB integers, laid out for reading one location's
forecast (a chunk is every hour of a 64 x 64 cell tile), and each hour's scales beside it. A run
is added in one commit and dropped by deleting its group; `maintain` then expires old snapshots
and garbage collects.

Icechunk reaches the object store through the object_store crate rather than its default AWS SDK
storage. The AWS SDK sends CRC32 checksums on bulk deletes, which ECS rejects ("Missing required
header for this request: Content-MD5"), so garbage collection would delete nothing; object_store
sends Content-MD5.

Design: docs/architecture/model-grid-storage-spike.md
"""

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import cached_property

import icechunk
import numpy as np
import zarr
from icechunk._icechunk_python import RepoUpdateRetryConfig  # not exported by icechunk
from wps_shared import config
from zarr.codecs import ZstdCodec
from zarr.codecs.numcodecs import PCodec

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.grids.grib import BC_LATITUDE, BC_LONGITUDE, Crop, GribScales, decode
from wps_weather_data.grids.models import MODELS, SCALES, VariableRun

logger = logging.getLogger(__name__)

TILE = 64
# How often a refused update of the repository is retried: about half a minute in all. Icechunk's
# default is 100 tries, over an hour. Updates only ever compete with the nightly maintenance, so a
# store that refuses for longer is stuck, and the job should fail and say so.
UPDATE_TRIES = 15
RUN_FORMAT = "%Y-%m-%dT%H"


def object_store_storage(prefix: str) -> icechunk.Storage:
    return icechunk.Storage.new_s3_object_store(
        icechunk.S3Options(
            region="us-east-1",
            endpoint_url=f"https://{config.get('OBJECT_STORE_SERVER')}",
            force_path_style=True,
        ),
        config.get("OBJECT_STORE_BUCKET"),
        prefix,
        icechunk.s3_static_credentials(
            access_key_id=config.get("OBJECT_STORE_USER_ID"),
            secret_access_key=config.get("OBJECT_STORE_SECRET"),
        ),
    )


def run_name(run_time: datetime) -> str:
    return f"{run_time.astimezone(UTC):{RUN_FORMAT}}"


class GridStore:
    """A model's `recent` or `history` store. Creating one does not contact the object store.
    With no `storage`, it is the one the addresser names, in our object store."""

    def __init__(self, model: str, store: str, storage: icechunk.Storage | None = None):
        self.model = MODELS[model]
        self.store = store
        self._storage = storage

    @cached_property
    def storage(self) -> icechunk.Storage:
        return self._storage or object_store_storage(
            StationWeatherAddresser().get_grid_key(self.model.name, self.store)
        )

    @cached_property
    def repository(self) -> icechunk.Repository:
        """The repository, created if it does not exist yet."""
        tries = icechunk.StorageRetriesSettings(max_tries=UPDATE_TRIES)
        config = icechunk.RepositoryConfig.default()
        config.repo_update_retries = RepoUpdateRetryConfig(default=tries)
        return icechunk.Repository.open_or_create(self.storage, config=config)

    def exists(self) -> bool:
        """Whether the repository exists, without creating it."""
        return icechunk.Repository.exists(self.storage)

    def _root(self) -> zarr.Group | None:
        """The latest snapshot's root group, or None while nothing has been written."""
        try:
            return zarr.open_group(self.repository.readonly_session("main").store, mode="r")
        except zarr.errors.GroupNotFoundError:
            return None

    def run_times(self) -> list[datetime]:
        """The runs the store holds, oldest first."""
        root = self._root()
        names = root.group_keys() if root is not None else []
        return sorted(datetime.strptime(n, RUN_FORMAT).replace(tzinfo=UTC) for n in names)

    def write_run(self, run_time: datetime, crop: Crop, variables: Iterable[VariableRun]) -> bool:
        """Add a run in one commit, a variable at a time. Returns False if the store already
        has it."""
        written, failures = write_run([self], run_time, crop, variables)
        if failures:
            raise failures[self]
        return bool(written)

    def _group(self, run_time: datetime) -> zarr.Group:
        root = self._root()
        name = run_name(run_time)
        if root is None or name not in root:
            raise KeyError(f"{self.store} has no {self.model.name} run {name}")
        return root[name]

    def _decode(self, group: zarr.Group, name: str, values: np.ndarray, hour) -> np.ndarray:
        scales = [group[f"{name}_{scale}"][hour] for scale in SCALES]
        if np.ndim(scales[0]):
            # Line each hour's scales up with the hour axis of the values.
            extra = (slice(None),) + (np.newaxis,) * (values.ndim - 1)
            scales = [scale[extra] for scale in scales]
        return decode(values, GribScales(*scales))

    def nearest_cell(self, latitude: float, longitude: float) -> tuple[int, int]:
        """The (y, x) of the grid cell nearest a location in BC."""
        if not (
            BC_LATITUDE[0] <= latitude <= BC_LATITUDE[1]
            and BC_LONGITUDE[0] <= longitude <= BC_LONGITUDE[1]
        ):
            raise ValueError(f"{latitude}, {longitude} is outside BC")
        root = self._root()
        if root is None:
            raise KeyError(f"{self.store} has no runs")
        lat, lon = root["latitude"][:], root["longitude"][:]
        distance = (lat - latitude) ** 2 + ((lon - longitude) * np.cos(np.radians(latitude))) ** 2
        y, x = np.unravel_index(np.argmin(distance), distance.shape)
        return int(y), int(x)

    def read_point(self, run_time: datetime, y: int, x: int) -> dict[str, np.ndarray]:
        """A grid cell's forecast for a run: each variable by forecast hour, and the hours."""
        group = self._group(run_time)
        point = {"forecast_hour": np.array(group.attrs["forecast_hours"])}
        for variable in self.model.variables:
            values = group[variable.name][:, y, x]
            point[variable.name] = self._decode(group, variable.name, values, slice(None))
        return point

    def read_map(self, run_time: datetime, hour: int, variable: str) -> np.ndarray:
        """A variable over BC at a forecast hour of a run, (y, x)."""
        group = self._group(run_time)
        index = list(group.attrs["forecast_hours"]).index(hour)
        return self._decode(group, variable, group[variable][index], index)

    def delete_runs_before(self, cutoff: datetime) -> list[datetime]:
        """Delete the runs that started before `cutoff`, in one commit. `maintain` reclaims
        their space. Returns the runs deleted."""
        old = [run_time for run_time in self.run_times() if run_time < cutoff]
        if old:
            session = self.repository.writable_session("main")
            root = zarr.open_group(session.store, mode="a")
            for run_time in old:
                del root[run_name(run_time)]
            session.commit(f"delete {self.model.name} runs before {run_name(cutoff)}")
            logger.info("Deleted %d %s runs from %s", len(old), self.model.name, self.store)
        return old

    def maintain(
        self,
        now: datetime,
        snapshot_retention: timedelta = timedelta(days=1),
        object_grace: timedelta = timedelta(hours=1),
    ) -> dict:
        """Expire snapshots older than `snapshot_retention` and delete the objects nothing left
        refers to. Objects written within `object_grace` are kept, so a run being written is not
        collected. Returns what garbage collection did."""
        expired = self.repository.expire_snapshots(older_than=now - snapshot_retention)
        summary = self.repository.garbage_collect(delete_object_older_than=now - object_grace)
        if summary.objects_failed_to_delete:
            logger.error(
                "Garbage collection of %s %s failed to delete %d objects: %s",
                self.model.name,
                self.store,
                summary.objects_failed_to_delete,
                summary.delete_errors,
            )
        return {
            "snapshots_expired": len(expired),
            "bytes_deleted": summary.bytes_deleted,
            "chunks_deleted": summary.chunks_deleted,
            "objects_failed_to_delete": summary.objects_failed_to_delete,
        }


class _RunWriter:
    """One run being written to one store, a variable at a time, until `commit`."""

    def __init__(self, store: GridStore, run_time: datetime, crop: Crop):
        self.store = store
        self.name = run_name(run_time)
        self.session = store.repository.writable_session("main")
        root = zarr.open_group(self.session.store, mode="a")
        self.exists = self.name in root
        if self.exists:
            return
        ny, nx = crop.latitude.shape
        if "latitude" not in root:
            for coordinate in ("latitude", "longitude"):
                data = getattr(crop, coordinate)
                root.create_array(coordinate, data=data, compressors=ZstdCodec(level=3))
        elif root["latitude"].shape != (ny, nx):
            raise ValueError(f"the store's grid is {root['latitude'].shape}, the run's {(ny, nx)}")
        hours = store.model.forecast_hours(run_time)
        self.group = root.create_group(self.name, attributes={"forecast_hours": list(hours)})
        self.chunks = (len(hours), TILE, TILE)
        # A variable's whole run is one object.
        self.shards = (len(hours), -(-ny // TILE) * TILE, -(-nx // TILE) * TILE)
        self.shape = (len(hours), ny, nx)

    def add(self, variable_run: VariableRun):
        variable = variable_run.variable
        array = self.group.create_array(
            variable.name,
            shape=self.shape,
            dtype="int32",
            fill_value=0,
            chunks=self.chunks,
            shards=self.shards,
            serializer=PCodec(level=8),
            compressors=None,
            dimension_names=("hour", "y", "x"),
            attributes={"units": variable.units},
        )
        array[:] = variable_run.integers
        for scale in SCALES:
            self.group.create_array(f"{variable.name}_{scale}", data=variable_run.scales[scale])

    def commit(self):
        model = self.store.model.name
        self.session.commit(f"{model} run {self.name}")
        logger.info("Wrote %s run %s to %s", model, self.name, self.store.store)


def write_run(
    stores: list[GridStore], run_time: datetime, crop: Crop, variables: Iterable[VariableRun]
) -> tuple[list[GridStore], dict[GridStore, Exception]]:
    """Add a run to each store that lacks it, a variable at a time: each variable is written to
    every store as it arrives, so only one is held at once, and each store commits once all are
    written. `variables` is only consumed if a store lacks the run.

    A store that fails does not stop the others. Returns the stores written, and the error of
    each that failed. An error reading `variables` is raised, with nothing committed."""
    for store in stores[1:]:
        if store.model != stores[0].model:
            raise ValueError("a run can only be written to stores of one model")
    writers: list[_RunWriter] = []
    failures: dict[GridStore, Exception] = {}
    for store in stores:
        with _recording_failure(store, run_time, failures):
            writer = _RunWriter(store, run_time, crop)
            if not writer.exists:
                writers.append(writer)
    if not writers:
        return [], failures
    expected = [v.name for v in stores[0].model.variables]
    received = []
    for variable_run in variables:
        received.append(variable_run.variable.name)
        for writer in writers:
            with _recording_failure(writer.store, run_time, failures):
                writer.add(variable_run)
        writers = [writer for writer in writers if writer.store not in failures]
        if not writers:
            return [], failures
    if received != expected:
        raise ValueError(f"the run has {received}, the model {expected}")
    written = []
    for writer in writers:
        with _recording_failure(writer.store, run_time, failures):
            writer.commit()
            written.append(writer.store)
    return written, failures


@contextmanager
def _recording_failure(store: GridStore, run_time: datetime, failures: dict[GridStore, Exception]):
    """Log an error writing a run to a store and record it in `failures`, instead of raising."""
    try:
        yield
    except Exception as error:
        name = f"{store.model.name} run {run_name(run_time)}"
        logger.exception("Failed to write %s to %s", name, store.store)
        failures[store] = error
