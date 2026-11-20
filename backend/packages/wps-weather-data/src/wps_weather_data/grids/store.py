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
from datetime import UTC, datetime, timedelta
from functools import cached_property

import icechunk
import numpy as np
import zarr
from wps_shared import config
from zarr.codecs import ZstdCodec
from zarr.codecs.numcodecs import PCodec

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.grids.grib import BC_LATITUDE, BC_LONGITUDE, GribScales, decode
from wps_weather_data.grids.models import MODELS, SCALES, RunGrid

logger = logging.getLogger(__name__)

TILE = 64
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
    def repository(self) -> icechunk.Repository:
        storage = self._storage or object_store_storage(
            StationWeatherAddresser().get_grid_key(self.model.name, self.store)
        )
        return icechunk.Repository.open_or_create(storage)

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

    def write_run(self, grid: RunGrid) -> bool:
        """Add a run in one commit. Returns False if the store already has it."""
        if grid.model.name != self.model.name:
            raise ValueError(f"a {grid.model.name} run cannot go in a {self.model.name} store")
        name = run_name(grid.run_time)
        session = self.repository.writable_session("main")
        root = zarr.open_group(session.store, mode="a")
        if name in root:
            return False
        ny, nx = grid.latitude.shape
        if "latitude" not in root:
            for coordinate in ("latitude", "longitude"):
                data = getattr(grid, coordinate)
                root.create_array(coordinate, data=data, compressors=ZstdCodec(level=3))
        elif root["latitude"].shape != (ny, nx):
            raise ValueError(f"the store's grid is {root['latitude'].shape}, the run's {(ny, nx)}")
        hours = len(self.model.hours)
        group = root.create_group(name, attributes={"forecast_hours": list(self.model.hours)})
        for variable in self.model.variables:
            array = group.create_array(
                variable.name,
                shape=(hours, ny, nx),
                dtype="int32",
                fill_value=0,
                chunks=(hours, TILE, TILE),
                # A variable's whole run is one object.
                shards=(hours, -(-ny // TILE) * TILE, -(-nx // TILE) * TILE),
                serializer=PCodec(level=8),
                compressors=None,
                dimension_names=("hour", "y", "x"),
                attributes={"units": variable.units},
            )
            array[:] = grid.integers[variable.name]
            for scale in SCALES:
                group.create_array(
                    f"{variable.name}_{scale}", data=grid.scales[variable.name][scale]
                )
        session.commit(f"{self.model.name} run {name}")
        logger.info("Wrote %s run %s to %s", self.model.name, name, self.store)
        return True

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
