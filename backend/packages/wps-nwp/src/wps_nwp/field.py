import asyncio
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property, partial

import numpy as np

from wps_nwp.variables import Native, Variable

_MISSING = 9.999e20
# Nearest-neighbour searches first look only at grid points this close to the query points.
_SEARCH_PAD_DEGREES = 1.0
# Cap on the size of the (query points x grid points) matrix built per chunk.
_CHUNK_ELEMENTS = 4_000_000
# How far past the first or last row or column, in cells, still counts as on the grid.
_EDGE_TOLERANCE = 1e-6
DEFAULT_WORKERS = 2


class Grid:
    """The location of every point of a model grid."""

    def __init__(self, shape: tuple[int, int], coordinates, axes: "_Axes | None" = None):
        """
        :param shape: rows and columns, the shape of Field.values
        :param coordinates: called once, if lats or lons are asked for, to get both as flat
            arrays. Deferred because sampling a regular grid never needs them.
        :param axes: how the grid is laid out, if it is regular enough to describe that way
        """
        self.shape = shape
        self._coordinates = coordinates
        self._axes = axes
        self._nearest: tuple[bytes, bytes, np.ndarray] | None = None
        self._lock = threading.Lock()

    @property
    def lats(self) -> np.ndarray:
        """Degrees north, same shape as Field.values."""
        return self._lat_lon[0]

    @property
    def lons(self) -> np.ndarray:
        """Degrees east in [-180, 180), same shape as Field.values."""
        return self._lat_lon[1]

    @cached_property
    def _lat_lon(self) -> tuple[np.ndarray, np.ndarray]:
        lats, lons = self._coordinates()
        self._coordinates = None  # it may be holding on to a GRIB message
        return lats.reshape(self.shape), _wrap(lons).reshape(self.shape)

    def nearest(self, lats, lons) -> np.ndarray:
        """
        Flat indices of the grid points nearest to each (lat, lon), by great-circle distance.

        Points outside a regional model's domain get its closest edge point, so check the
        domain yourself if that matters. The most recent result is remembered, which makes
        sampling many fields at the same points cost one search.
        """
        lats = np.atleast_1d(np.asarray(lats, dtype=float))
        lons = np.atleast_1d(np.asarray(lons, dtype=float))
        if lats.size == 0:
            return np.empty(0, dtype=np.intp)
        key = (lats.tobytes(), lons.tobytes())
        with self._lock:  # fields are sampled from several threads at once; search once
            if self._nearest is None or self._nearest[:2] != key:
                self._nearest = (*key, self._locate(lats, lons))
            return self._nearest[2]

    def _locate(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        if self._axes is None:
            return self._search(lats, lons)
        result, inside = self._axes.nearest(lats, lons)
        if not inside.all():
            # Off the edge of a regional grid the nearest point is not just the nearest row
            # and column, so those locations are searched for the long way.
            result[~inside] = self._search(lats[~inside], lons[~inside])
        return result

    def _search(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """Nearest points on any grid, by comparing against the coordinates of its points."""
        grid_lats, grid_lons = self.lats.ravel(), self.lons.ravel()
        points = _unit_vectors(lats, lons)

        # Global grids have millions of points, so start with the ones in a box around the
        # query points, sized to hold every grid point within pad degrees of any of them.
        pad = _SEARCH_PAD_DEGREES
        box = (grid_lats >= lats.min() - pad) & (grid_lats <= lats.max() + pad)
        highest_latitude = np.abs(lats).max() + pad
        if highest_latitude < 85:  # nearer the poles a degree of distance spans any longitude
            lons_radians = np.radians(lons)
            centre = np.degrees(np.arctan2(np.sin(lons_radians).sum(), np.cos(lons_radians).sum()))
            half_width = np.abs(_wrap(lons - centre)).max()
            half_width += 1.1 * pad / np.cos(np.radians(highest_latitude))
            if half_width < 180:
                box &= np.abs(_wrap(grid_lons - centre)) <= half_width
        candidates = np.flatnonzero(box)

        result = np.zeros(len(points), dtype=np.intp)
        outside = np.ones(len(points), dtype=bool)
        if candidates.size:
            index, cosine = _closest(points, grid_lats[candidates], grid_lons[candidates])
            result = candidates[index]
            # A match within pad degrees is the true nearest, as nothing closer was left out
            # of the box. Anything further is searched for again across the whole grid.
            outside = cosine < np.cos(np.radians(pad))
        if outside.any():
            result[outside], _ = _closest(points[outside], grid_lats, grid_lons)
        return result


@dataclass(frozen=True, eq=False)
class _Axes:
    """
    A grid with evenly spaced rows of latitude and columns of longitude, which covers every
    lat/lon model and, once the pole is rotated, the rotated ones (RDPS, HRDPS).

    On such a grid the nearest point to a location is one of the four around it, so it can
    be found from the layout alone, without the coordinates of every grid point.
    """

    first_lat: float
    lat_step: float  # from one row to the next; negative when rows run north to south
    rows: int
    first_lon: float
    lon_step: float  # from one column to the next
    columns: int
    rotation: np.ndarray | None  # turns a true unit vector into one in the rotated frame

    def nearest(self, lats: np.ndarray, lons: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Flat index of the nearest grid point, and whether each location is within the grid."""
        points = _unit_vectors(lats, lons)
        if self.rotation is not None:
            # Rotating the sphere keeps distances, so nearest in the rotated frame is nearest.
            points = points @ self.rotation.T
            lats = np.degrees(np.arcsin(np.clip(points[:, 2], -1, 1)))
            lons = np.degrees(np.arctan2(points[:, 1], points[:, 0]))

        row = (lats - self.first_lat) / self.lat_step
        column = ((lons - self.first_lon) * np.sign(self.lon_step) % 360) / abs(self.lon_step)
        wraps = self.columns * abs(self.lon_step) > 360 - _EDGE_TOLERANCE
        inside = (row >= -_EDGE_TOLERANCE) & (row <= self.rows - 1 + _EDGE_TOLERANCE)
        if not wraps:
            inside &= column <= self.columns - 1 + _EDGE_TOLERANCE

        below = np.clip(np.floor(row), 0, self.rows - 1).astype(np.intp)
        left = np.floor(column).astype(np.intp)
        best_index = np.zeros(len(points), dtype=np.intp)
        best_cosine = np.full(len(points), -np.inf)
        for r in (below, np.minimum(below + 1, self.rows - 1)):
            for c in (left, left + 1):
                c = c % self.columns if wraps else np.clip(c, 0, self.columns - 1)
                corner = _unit_vectors(
                    self.first_lat + r * self.lat_step, self.first_lon + c * self.lon_step
                )
                cosine = (points * corner).sum(axis=1)
                closer = cosine > best_cosine
                best_index[closer] = (r * self.columns + c)[closer]
                best_cosine[closer] = cosine[closer]
        return best_index, inside


def _wrap(degrees):
    return (degrees + 180) % 360 - 180


def _unit_vectors(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    lat, lon = np.radians(lats), np.radians(lons)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def _closest(points: np.ndarray, grid_lats: np.ndarray, grid_lons: np.ndarray):
    """Index of, and cosine of the angle to, the grid point closest to each unit vector."""
    grid = _unit_vectors(grid_lats, grid_lons).T
    index = np.empty(len(points), dtype=np.intp)
    cosine = np.empty(len(points))
    rows = max(1, _CHUNK_ELEMENTS // grid.shape[1])
    for start in range(0, len(points), rows):
        chunk = slice(start, start + rows)
        dots = points[chunk] @ grid
        index[chunk] = dots.argmax(axis=1)
        cosine[chunk] = dots.max(axis=1)
    return index, cosine


@dataclass(frozen=True, eq=False)
class Field:
    """
    One variable at one forecast step, as a GRIB2 message that is decoded on first use.

    Fetching and decoding are separate so that the raw message can be stored or forwarded
    without paying for a decode.
    """

    model: str
    variable: Variable | Native
    run: datetime
    step: int  # hours after run
    url: str
    grib: bytes = field(repr=False)

    @property
    def valid_time(self) -> datetime:
        return self.run + timedelta(hours=self.step)

    @property
    def values(self) -> np.ndarray:
        """2D array in the order the model stores it, NaN where missing. See grid for locations."""
        return self._decoded[0]

    @property
    def grid(self) -> Grid:
        return self._decoded[1]

    @property
    def units(self) -> str:
        """The Variable's units, or for a Native field whatever the GRIB message declares."""
        if isinstance(self.variable, Variable):
            return self.variable.units
        return self._decoded[2]

    def sample(self, lats, lons) -> np.ndarray:
        """
        Values at the grid points nearest to each (lat, lon).

        Unlike values, this does not keep the decoded grid on the field, so sampling every
        field of a run costs the memory of one grid rather than one per field.
        """
        values, grid, _ = self.__dict__.get("_decoded") or self._decode()
        return values.ravel()[grid.nearest(lats, lons)]

    @cached_property
    def _decoded(self) -> tuple[np.ndarray, Grid, str]:
        return self._decode()

    def _decode(self) -> tuple[np.ndarray, Grid, str]:
        values, grid, units = _decode(self.grib)
        # Every supported model encodes the Variables in the same units, bar one: ECMWF
        # reports precipitation in metres where the others use kg m-2, which is mm.
        if self.variable is Variable.PRECIP and units == "m":
            values *= 1000
        return values, grid, units


async def sample(
    fields: Iterable[Field], lats, lons, *, workers: int = DEFAULT_WORKERS
) -> list[np.ndarray]:
    """
    Field.sample for several fields at once, decoded in worker threads.

    Decoding takes a few milliseconds for ECMWF and NOAA fields but a few hundred for ECCC's,
    which are JPEG2000. Awaiting this rather than calling Field.sample in a loop leaves the
    event loop free to keep downloading meanwhile, and decodes on more than one core.

    :param workers: fields decoded at a time. Each costs a decoded grid of memory while it
        runs, and more than the number of cores available gains nothing.
    :return: one array per field, in the order given
    """
    limit = asyncio.Semaphore(workers)

    async def one(field: Field) -> np.ndarray:
        async with limit:
            return await asyncio.to_thread(field.sample, lats, lons)

    return await asyncio.gather(*(one(field) for field in fields))


# Fields from the same model share a grid, so each distinct grid is described once and kept
# for the life of the process.
_grids: dict[str, Grid] = {}
_grids_lock = threading.Lock()


def _eccodes():
    """
    The eccodes module, imported on first use.

    It is an optional dependency, since fetching and storing GRIB does not need it, and
    loading its library is not free.
    """
    try:
        import eccodes
    except ImportError as error:
        raise ImportError(
            "Reading values from a field needs eccodes. Install wps-nwp[decode]."
        ) from error
    return eccodes


def _decode(grib: bytes) -> tuple[np.ndarray, Grid, str]:
    eccodes = _eccodes()

    handle = eccodes.codes_new_from_message(grib)
    try:
        has_bitmap = eccodes.codes_get(handle, "bitmapPresent")
        if has_bitmap:
            eccodes.codes_set(handle, "missingValue", _MISSING)
        values = eccodes.codes_get_values(handle)
        if has_bitmap:
            values[values == _MISSING] = np.nan
        units = eccodes.codes_get(handle, "units")

        grid_key = eccodes.codes_get(handle, "md5GridSection")
        with _grids_lock:
            grid = _grids.get(grid_key)
            if grid is None:
                shape = (eccodes.codes_get(handle, "Ny"), eccodes.codes_get(handle, "Nx"))
                grid = _grids[grid_key] = Grid(shape, partial(_coordinates, grib), _axes(handle))
    finally:
        eccodes.codes_release(handle)
    return values.reshape(grid.shape), grid, units


def _coordinates(grib: bytes) -> tuple[np.ndarray, np.ndarray]:
    """Latitude and longitude of every grid point of a message, in the order of its values."""
    eccodes = _eccodes()

    handle = eccodes.codes_new_from_message(grib)
    try:
        return (
            eccodes.codes_get_array(handle, "latitudes"),
            eccodes.codes_get_array(handle, "longitudes"),
        )
    finally:
        eccodes.codes_release(handle)


def _axes(handle) -> _Axes | None:
    """The layout of a message's grid, or None if it is not one _Axes can describe."""
    eccodes = _eccodes()

    def get(key: str):
        return eccodes.codes_get(handle, key)

    grid_type = get("gridType")
    rows, columns = get("Nj"), get("Ni")
    if (
        grid_type not in ("regular_ll", "rotated_ll")
        or get("jPointsAreConsecutive")
        or get("alternativeRowScanning")
        or rows < 2
        or columns < 2
    ):
        return None

    rotation = None
    if grid_type == "rotated_ll":
        if get("angleOfRotationInDegrees"):
            return None
        # The rotated frame has its south pole at the given point, and its origin a quarter
        # turn north of there along the same meridian.
        pole_lat = get("latitudeOfSouthernPoleInDegrees")
        pole_lon = get("longitudeOfSouthernPoleInDegrees")
        up = -_unit_vectors(np.array(pole_lat), np.array(pole_lon))
        origin = _unit_vectors(np.array(pole_lat + 90), np.array(pole_lon))
        rotation = np.stack([origin, np.cross(up, origin), up])

    # The spacing is taken from the first and last points rather than the increment in the
    # message, which is rounded to a millionth of a degree and drifts over a thousand rows.
    first_lat, last_lat = (
        get("latitudeOfFirstGridPointInDegrees"),
        get("latitudeOfLastGridPointInDegrees"),
    )
    first_lon, last_lon = (
        get("longitudeOfFirstGridPointInDegrees"),
        get("longitudeOfLastGridPointInDegrees"),
    )
    eastward = -1 if get("iScansNegatively") else 1
    return _Axes(
        first_lat=first_lat,
        lat_step=(last_lat - first_lat) / (rows - 1),
        rows=rows,
        first_lon=first_lon,
        lon_step=eastward * ((last_lon - first_lon) * eastward % 360) / (columns - 1),
        columns=columns,
        rotation=rotation,
    )


def extract(raw: bytes, subfield: int | None = None) -> bytes:
    """
    Check that raw is a complete GRIB message and return the one field asked for.

    NOAA packs related fields (the u and v wind components, typically) into a single GRIB2
    message. eccodes only reads the first field of a message held in memory, so subfield
    picks one out and rebuilds it as a message of its own.
    """
    if raw[:4] != b"GRIB" or raw[-4:] != b"7777":
        raise ValueError("not a complete GRIB message")
    if subfield is None:
        return raw

    # GRIB2: a 16 byte indicator section, numbered sections each starting with a 4 byte
    # length and a 1 byte number, then "7777". Sections 2-7, 3-7 or 4-7 repeat once per
    # field, and a field inherits whichever earlier sections it does not repeat.
    body = memoryview(raw)[16:-4]
    sections: dict[int, bytes] = {}
    position = 0
    fields_seen = 0
    while position < len(body):
        length = int.from_bytes(body[position : position + 4])
        number = body[position + 4]
        if length < 5 or number not in range(1, 8):
            raise ValueError("malformed GRIB2 message")
        sections[number] = bytes(body[position : position + length])
        position += length
        if number == 7:
            if fields_seen == subfield:
                payload = b"".join(sections[n] for n in sorted(sections))
                total = 16 + len(payload) + 4
                return raw[:8] + total.to_bytes(8) + payload + b"7777"
            fields_seen += 1
    raise ValueError(f"GRIB message has {fields_seen} fields, wanted number {subfield + 1}")
