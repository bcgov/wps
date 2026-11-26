"""Reading GRIB2 fields as their packed integers, cropped to BC.

A GRIB2 value is stored as an integer X, with value = (R + X * 2**E) / 10**D: R is the field's
reference value, E its binary scale and D its decimal scale. Keeping X with R, E and D keeps
exactly what the provider published, in fewer bytes than the decoded floats.
"""

from pathlib import Path
from typing import NamedTuple

import eccodes
import numpy as np

# Generous BC bounds; a rotated grid makes the crop a little larger.
BC_LATITUDE = (48.2, 60.1)
BC_LONGITUDE = (-139.2, -114.0)


class GribScales(NamedTuple):
    """What turns a field's packed integers into its values. `decode` takes one of each, or an
    array of each with a value for every forecast hour.

    :param reference: R, roughly the field's lowest value, before dividing by 10**D
    :param binary_scale: E
    :param decimal_scale: D
    """

    reference: float
    binary_scale: int
    decimal_scale: int


def decode(integers: np.ndarray, scales: GribScales) -> np.ndarray:
    """The values of packed integers, (R + X * 2**E) / 10**D.

    :param integers: The packed integers, X
    :param scales: Their scales, of a shape that broadcasts to the integers'
    :return: The values, as float64, in the field's units
    """
    return (scales.reference + integers * 2.0**scales.binary_scale) / 10.0**scales.decimal_scale


def grib_integers(values: np.ndarray, scales: GribScales) -> np.ndarray:
    """The integers a field stored for its decoded `values`.

    Every value sits on the field's grid of steps, to within float64 rounding, so rounding
    recovers the integer exactly.

    :param values: The field's decoded values
    :param scales: The field's scales
    :return: The integers, as int32
    :raises ValueError: If a value is off the field's steps, or does not decode back to the same
        float32, rather than store something other than what was published
    """
    unrounded = (values * 10.0**scales.decimal_scale - scales.reference) / 2.0**scales.binary_scale
    integers = np.rint(unrounded)
    if np.abs(unrounded - integers).max() > 1e-6 or not np.array_equal(
        decode(integers, scales).astype(np.float32), values.astype(np.float32)
    ):
        raise ValueError("the field does not round-trip through its GRIB integers")
    return integers.astype(np.int32)


def read_field(path: Path) -> tuple[np.ndarray, GribScales]:
    """Read a GRIB file's field.

    :param path: A GRIB file of one message
    :return: The field's values, as (rows, columns) float64, and its scales
    """
    with open(path, "rb") as grib:
        handle = eccodes.codes_grib_new_from_file(grib)
    try:
        shape = (eccodes.codes_get(handle, "Nj"), eccodes.codes_get(handle, "Ni"))
        values = eccodes.codes_get_values(handle).reshape(shape)
        scales = GribScales(
            eccodes.codes_get(handle, "referenceValue"),
            eccodes.codes_get(handle, "binaryScaleFactor"),
            eccodes.codes_get(handle, "decimalScaleFactor"),
        )
    finally:
        eccodes.codes_release(handle)
    return values, scales


class Crop(NamedTuple):
    """The part of a model's grid that covers BC.

    :param y: The grid's rows
    :param x: The grid's columns
    :param latitude: The cells' latitudes, (y, x)
    :param longitude: The cells' longitudes, (y, x), from -180 to 180
    """

    y: slice
    x: slice
    latitude: np.ndarray
    longitude: np.ndarray


def bc_crop(path: Path) -> Crop:
    """The part of a file's grid that covers BC.

    :param path: A GRIB file of one message
    :return: The rows and columns covering BC, and their latitudes and longitudes
    :raises ValueError: If the grid has no cells in BC
    """
    with open(path, "rb") as grib:
        handle = eccodes.codes_grib_new_from_file(grib)
    try:
        shape = (eccodes.codes_get(handle, "Nj"), eccodes.codes_get(handle, "Ni"))
        latitude = eccodes.codes_get_array(handle, "latitudes").reshape(shape)
        longitude = eccodes.codes_get_array(handle, "longitudes").reshape(shape)
    finally:
        eccodes.codes_release(handle)
    longitude = np.where(longitude > 180, longitude - 360, longitude)
    inside = (
        (latitude >= BC_LATITUDE[0])
        & (latitude <= BC_LATITUDE[1])
        & (longitude >= BC_LONGITUDE[0])
        & (longitude <= BC_LONGITUDE[1])
    )
    if not inside.any():
        raise ValueError(f"{path.name} does not cover BC")
    rows, columns = np.flatnonzero(inside.any(axis=1)), np.flatnonzero(inside.any(axis=0))
    y, x = slice(rows[0], rows[-1] + 1), slice(columns[0], columns[-1] + 1)
    return Crop(y, x, latitude[y, x].astype(np.float32), longitude[y, x].astype(np.float32))
