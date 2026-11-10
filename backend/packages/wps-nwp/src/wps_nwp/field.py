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
# Standard gravity, which ECMWF divides geopotential by to get height: m s-2.
_GRAVITY = 9.80665


class Grid:
    """The location of every point of a model grid."""

    def __init__(self, shape: tuple[int, int], coordinates, axes: "_Axes | None" = None):
        """
        :param shape: rows and columns, the shape of Field.values
        :param coordinates: called once, if lats or lons are asked for, to get both as flat
            arrays. Deferred because sampling a regular grid never needs them.
        :param axes: how the grid is laid out, if it is regular enough to describe that way

        Nothing is computed here: the grid only records how to find things out later.
        """
        self.shape = shape
        self._coordinates = coordinates
        self._axes = axes
        self._nearest: tuple[bytes, bytes, np.ndarray] | None = None
        self._lock = threading.Lock()

    @property
    def lats(self) -> np.ndarray:
        """
        Degrees north, same shape as Field.values.

        Worked out for the whole grid on first access, along with lons, and then kept.
        """
        return self._lat_lon[0]

    @property
    def lons(self) -> np.ndarray:
        """
        Degrees east in [-180, 180), same shape as Field.values.

        Worked out for the whole grid on first access, along with lats, and then kept.
        """
        return self._lat_lon[1]

    @cached_property
    def _lat_lon(self) -> tuple[np.ndarray, np.ndarray]:
        """
        The latitude and longitude of every grid point, worked out once.

        Calls the coordinates function the grid was built with, reshapes both arrays to the
        grid's rows and columns, and brings longitudes into [-180, 180). The function is then
        let go of, because it holds the GRIB message this grid was first seen in.
        """
        lats, lons = self._coordinates()
        self._coordinates = None  # it may be holding on to a GRIB message
        return lats.reshape(self.shape), _wrap(lons).reshape(self.shape)

    def nearest(self, lats, lons) -> np.ndarray:
        """
        Flat indices of the grid points nearest to each (lat, lon), by great-circle distance.

        Points outside a regional model's domain get its closest edge point, so check the
        domain yourself if that matters. The most recent result is remembered, which makes
        sampling many fields at the same points cost one search.

        An index is into the flattened grid, as in Field.values.ravel()[index].

        How it works: the locations are converted to float arrays, and their raw bytes are
        the key to the remembered result. If they are the locations of the previous call, the
        indices found then are returned. Otherwise _locate does the search and its result
        replaces the remembered one. The lock makes threads that ask at the same moment wait
        for one search rather than each doing their own.
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

    def x_axis_angle(self, index) -> np.ndarray:
        """
        The direction the grid's x axis points at each grid point, in radians anticlockwise
        from true east.

        It is 0 everywhere on a regular lat/lon grid, but not on a rotated or projected one,
        where it is what turns vectors given relative to the grid into true ones.

        How it works: the direction from the grid point before each one in its row to the
        one after it is worked out from their latitudes and longitudes, on a plane tangent to
        the earth. Spanning the point from both sides makes this accurate to a small fraction
        of the angle by which the axis turns from one cell to the next. The first and last
        points of a row use themselves in place of the neighbour they lack. This uses the
        coordinates of the grid's points, which are worked out on first use.

        :param index: flat indices of grid points, as returned by nearest
        """
        rows, columns = np.divmod(np.asarray(index), self.shape[1])
        before = np.maximum(columns - 1, 0)
        after = np.minimum(columns + 1, self.shape[1] - 1)
        lats, lons = self.lats, self.lons
        start_lat, start_lon = lats[rows, before], lons[rows, before]
        end_lat, end_lon = lats[rows, after], lons[rows, after]
        middle_lat = np.radians((start_lat + end_lat) / 2)
        east = _wrap(end_lon - start_lon) * np.cos(middle_lat)
        north = end_lat - start_lat
        return np.arctan2(north, east)

    def _locate(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """
        Find the nearest grid points by the cheapest method that is exact.

        A grid with a regular layout is searched arithmetically by _Axes.nearest, which needs
        no coordinates. Locations it reports as outside the grid, and every location on any
        other kind of grid, go through _search instead.
        """
        if self._axes is None:
            return self._search(lats, lons)
        result, inside = self._axes.nearest(lats, lons)
        if not inside.all():
            # Off the edge of a regional grid the nearest point is not just the nearest row
            # and column, so those locations are searched for the long way.
            result[~inside] = self._search(lats[~inside], lons[~inside])
        return result

    def _search(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """
        Nearest points on any grid, by comparing against the coordinates of its points.

        Locations and grid points are turned into unit vectors on the sphere, where the
        nearest point is the one with the largest dot product. Comparing every location with
        every point of a grid of millions is slow, so it is done in two passes:

        1. Only the grid points inside a latitude and longitude box around the locations are
           compared. The box is padded by _SEARCH_PAD_DEGREES. In longitude the pad is divided
           by the cosine of the highest latitude, because a degree of distance spans more
           longitude towards the poles. The longitude limits are dropped altogether above 85
           degrees, or when the box would reach round the globe.
        2. A match nearer than the pad is certain to be the true nearest, because every grid
           point that near is inside the box. Any location whose best match is further away,
           or for which the box held no points, is compared against the whole grid.
        """
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
        """
        Flat index of the nearest grid point, and whether each location is within the grid.

        1. On a rotated grid the locations are first turned into the rotated frame, in which
           the grid is an ordinary lat/lon grid. Rotating the sphere keeps distances, so the
           nearest point there is the nearest point.
        2. Each location is expressed in fractional rows and columns from the first grid
           point. Longitude is taken modulo 360 in the direction the columns run, so it makes
           no difference whether the grid counts from -180 or from 0.
        3. The nearest grid point is one of the four corners of the cell the location is in.
           The great-circle distance to each corner is compared, as a dot product of unit
           vectors, and the nearest kept. Rounding the row and the column separately would
           not do, because columns draw together towards the pole. On a grid that goes all
           the way round, the column after the last is the first.

        A location is within the grid if its row is between the first and the last and, on a
        grid that does not go all the way round, its column is too. For a location outside,
        the index is only the nearest corner of the cell at the edge, and the caller has to
        search for the true nearest point.
        """
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
    """Bring angles in degrees into [-180, 180)."""
    return (degrees + 180) % 360 - 180


def _unit_vectors(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """
    Points on the unit sphere for latitudes and longitudes in degrees.

    The result has a last axis of (x, y, z). The dot product of two such vectors is the
    cosine of the angle between the two places, so the largest dot product is the nearest.
    """
    lat, lon = np.radians(lats), np.radians(lons)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def _closest(points: np.ndarray, grid_lats: np.ndarray, grid_lons: np.ndarray):
    """
    Index of, and cosine of the angle to, the grid point closest to each unit vector.

    The locations' vectors are multiplied by the grid points' in one matrix product, and the
    largest entry in each row is that location's nearest point. The product has a row per
    location and a column per grid point, so locations are taken a few at a time to keep it
    under _CHUNK_ELEMENTS elements.
    """
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
        """The time the forecast is for: the run time plus the step in hours."""
        return self.run + timedelta(hours=self.step)

    @property
    def values(self) -> np.ndarray:
        """
        2D array in the order the model stores it, NaN where missing. See grid for locations.

        The message is decoded on first access and the result kept on the field, which costs
        a whole grid of memory for as long as the field is alive. Use sample when only the
        values at some locations are wanted.
        """
        return self._decoded[0]

    @property
    def grid(self) -> Grid:
        """
        Where each of values is on the earth.

        Fields on the same model grid share one Grid. Like values, this decodes the message
        on first access and keeps the result.
        """
        return self._decoded[1]

    @property
    def units(self) -> str:
        """
        The Variable's units, or for a Native field whatever the GRIB message declares.

        A Variable's units are fixed, so nothing is decoded. A Native field is decoded, on
        first access, to read them from the message.
        """
        if isinstance(self.variable, Variable):
            return self.variable.units
        return self._decoded[2]

    def sample(self, lats, lons) -> np.ndarray:
        """
        Values at the grid points nearest to each (lat, lon).

        Unlike values, this does not keep the decoded grid on the field, so sampling every
        field of a run costs the memory of one grid rather than one per field.

        How it works: if values has already been read, that decoded array is used. Otherwise
        the message is decoded, the points wanted are picked out of it with the indices from
        Grid.nearest, and the decoded array is thrown away.
        """
        values, grid, _ = self.__dict__.get("_decoded") or self._decode()
        return values.ravel()[grid.nearest(lats, lons)]

    @cached_property
    def _decoded(self) -> tuple[np.ndarray, Grid, str]:
        """
        The decoded values, grid and units, computed on first access and kept on the field.

        This is what values, grid and units read from.
        """
        return self._decode()

    def _decode(self) -> tuple[np.ndarray, Grid, str]:
        """
        Decode the message without keeping the result.

        Returns the values, their grid and the units the message declares. Every supported
        model encodes the Variables in the units Variable.units gives, bar two from ECMWF,
        which are converted in place: precipitation in metres is multiplied by 1000 to give
        mm, and terrain, published as surface geopotential, is divided by standard gravity
        to give its height. Nothing else is converted.
        """
        values, grid, units = _decode(self.grib)
        if self.variable is Variable.PRECIP and units == "m":
            values *= 1000
        elif self.variable is Variable.SURFACE_HEIGHT and units == "m**2 s**-2":
            values /= _GRAVITY
        return values, grid, units

    @property
    def relative_to_grid(self) -> bool:
        """
        Whether the message gives vector components relative to its grid's axes rather than
        to true east and north. It only means anything for a wind component.
        """
        eccodes = _eccodes()
        handle = eccodes.codes_new_from_message(self.grib)
        try:
            return bool(eccodes.codes_get(handle, "uvRelativeToGrid"))
        finally:
            eccodes.codes_release(handle)


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

    How it works: each field's sample runs in a thread from asyncio's default pool. That
    runs in parallel because the decoder releases the interpreter lock while it works. A
    semaphore lets at most workers of them run at a time, and the rest wait their turn.
    """
    limit = asyncio.Semaphore(workers)

    async def one(field: Field) -> np.ndarray:
        """Sample one field in a worker thread, once a worker is free."""
        async with limit:
            return await asyncio.to_thread(field.sample, lats, lons)

    return await asyncio.gather(*(one(field) for field in fields))


def wind(u: Field, v: Field, lats, lons) -> tuple[np.ndarray, np.ndarray]:
    """
    Wind speed, and the direction the wind blows from, at each (lat, lon).

    Use it rather than working these out from sampled components, because on rotated and
    projected grids (RDPS, HRDPS, NAM, RRFS) the components are relative to the grid, not
    to true north, and a direction worked out from them as they stand is wrong by up to
    tens of degrees. Speed is the same either way.

    How it works: both fields are decoded, without keeping the result, and sampled at the
    grid points nearest to the locations. If the u field says its components are relative
    to the grid, they are turned through the angle Grid.x_axis_angle gives at each of those
    points, which makes them true east and north components. Speed and direction follow from
    those.

    :param u: the eastward, or grid x, component, from U10 or a Native field
    :param v: the matching northward, or grid y, component, for the same step
    :return: speed in the fields' units (m s-1 for the Variables), and direction in degrees
        clockwise from true north
    :raises ValueError: u and v are not on the same grid
    """
    u_values, grid, _ = u.__dict__.get("_decoded") or u._decode()
    v_values, v_grid, _ = v.__dict__.get("_decoded") or v._decode()
    if v_grid is not grid:
        raise ValueError("u and v are on different grids")

    index = grid.nearest(lats, lons)
    east, north = u_values.ravel()[index], v_values.ravel()[index]
    if u.relative_to_grid:
        angle = grid.x_axis_angle(index)
        east, north = (
            east * np.cos(angle) - north * np.sin(angle),
            east * np.sin(angle) + north * np.cos(angle),
        )
    speed = np.hypot(east, north)
    direction = (270 - np.degrees(np.arctan2(north, east))) % 360
    return speed, direction


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
    """
    Decode a GRIB message into its values, its grid and its units.

    eccodes unpacks the values as a flat float64 array. If the message has a bitmap marking
    points with no value, eccodes is told to write a sentinel at those points, which is then
    replaced by NaN.

    The grid is looked up by the checksum eccodes computes over the message's grid
    definition. The first message seen on a grid creates its Grid, with the layout read from
    the header and the coordinates left to be worked out later if anything asks for them.
    Every later message on that grid reuses it. The lock stops two threads that decode at the
    same moment from each creating it.

    The values are returned reshaped to the grid's rows and columns, in the order the
    message stores them.
    """
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
    """
    Latitude and longitude of every grid point of a message, in the order of its values.

    eccodes works them out from the message's grid definition, which it can do for any kind
    of grid. For a grid of millions of points that is slow and large, which is why Grid only
    calls this if it has to.
    """
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
    """
    The layout of a message's grid, or None if it is not one _Axes can describe.

    A grid qualifies if it is a regular or rotated lat/lon grid, stored row by row with
    every row running the same way, and has at least two rows and two columns.

    For a rotated grid a 3x3 matrix is built whose rows are the axes of the rotated frame,
    written in true coordinates. Multiplying a true unit vector by it gives the same point
    in the rotated frame. A grid that is also turned about its own pole is left to the
    general search.

    The first grid point comes from the header. The spacing is the distance from the first
    point to the last divided by the number of gaps. For longitude that distance is taken
    modulo 360 in the direction the columns run, so that a grid crossing the 0 or 180
    meridian comes out right.
    """
    eccodes = _eccodes()

    def get(key: str):
        """Read one key from the message header."""
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

    How it works: a complete message starts with "GRIB" and ends with "7777", and anything
    else raises ValueError. With no subfield the message is returned as it is. Otherwise its
    sections are walked in order, remembering the latest copy of each numbered section. A
    field is complete each time a section 7, the data, has been read. When the field wanted
    is reached, the remembered sections are joined in order behind a copy of the indicator
    section with the new total length written into it, and "7777" is added to the end.

    :param subfield: which field of the message to return, counting from 0, or None for a
        message that holds one field
    :raises ValueError: raw is not a complete message, or has no such field
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
