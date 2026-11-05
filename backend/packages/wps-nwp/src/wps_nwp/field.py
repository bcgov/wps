from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property

import numpy as np

from wps_nwp.variables import Native, Variable

_MISSING = 9.999e20
# Nearest-neighbour searches first look only at grid points this close to the query points.
_SEARCH_PAD_DEGREES = 1.0
# Cap on the size of the (query points x grid points) matrix built per chunk.
_CHUNK_ELEMENTS = 4_000_000


class Grid:
    """The location of every point of a model grid."""

    def __init__(self, lats: np.ndarray, lons: np.ndarray):
        self.lats = lats  # degrees north, same shape as Field.values
        self.lons = lons  # degrees east in [-180, 180)
        self.shape = lats.shape
        self._nearest: tuple[bytes, bytes, np.ndarray] | None = None

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
        if self._nearest is None or self._nearest[:2] != key:
            self._nearest = (*key, self._search(lats, lons))
        return self._nearest[2]

    def _search(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
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
        """Values at the grid points nearest to each (lat, lon)."""
        return self.values.ravel()[self.grid.nearest(lats, lons)]

    @cached_property
    def _decoded(self) -> tuple[np.ndarray, Grid, str]:
        values, grid, units = _decode(self.grib)
        # Every supported model encodes the Variables in the same units, bar one: ECMWF
        # reports precipitation in metres where the others use kg m-2, which is mm.
        if self.variable is Variable.PRECIP and units == "m":
            values = values * 1000
        return values, grid, units


# Fields from the same model share a grid, and working out where its points are costs far
# more than decoding the values, so grids are kept for the life of the process.
_grids: dict[str, Grid] = {}


def _decode(grib: bytes) -> tuple[np.ndarray, Grid, str]:
    # Imported here so that fetching without decoding does not load the eccodes library.
    import eccodes

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
        grid = _grids.get(grid_key)
        if grid is None:
            shape = (eccodes.codes_get(handle, "Ny"), eccodes.codes_get(handle, "Nx"))
            lats = eccodes.codes_get_array(handle, "latitudes").reshape(shape)
            lons = _wrap(eccodes.codes_get_array(handle, "longitudes")).reshape(shape)
            grid = _grids[grid_key] = Grid(lats, lons)
    finally:
        eccodes.codes_release(handle)
    return values.reshape(grid.shape), grid, units


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
