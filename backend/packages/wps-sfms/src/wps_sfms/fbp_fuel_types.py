"""Fuel-grid classifications used by SFMS fire behaviour calculations."""

from types import MappingProxyType
from typing import Mapping

import numpy as np
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.fuel_types import FuelTypeEnum

# BC base fuel grid values (fuel_type_raster) translated to the national FBP fuel lookup grid
# values used by temporal fuel grids. Leafless/matted variants are the off-season defaults.
NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE: Mapping[int, int] = MappingProxyType(
    {
        1: 1,  # C-1
        2: 2,  # C-2
        3: 3,  # C-3
        4: 4,  # C-4
        5: 5,  # C-5
        6: 6,  # C-6
        7: 7,  # C-7
        8: 11,  # D-1
        9: 21,  # S-1
        10: 22,  # S-2
        11: 23,  # S-3
        12: 31,  # O-1a
        13: 70,  # M-3
        14: 40,  # M-1
        99: 101,  # Non-fuel
        102: 102,  # Water
    }
)

# national grid values swapped from leafless to green during the green-up period
GREEN_UP_GRID_VALUES: Mapping[int, int] = MappingProxyType({11: 12, 40: 50, 70: 80})

# national FBP fuel lookup grid values found in temporal fuel grids
FUEL_TYPES_BY_GRID_VALUE: Mapping[int, FuelTypeEnum] = MappingProxyType(
    {
        1: FuelTypeEnum.C1,
        2: FuelTypeEnum.C2,
        3: FuelTypeEnum.C3,
        4: FuelTypeEnum.C4,
        5: FuelTypeEnum.C5,
        6: FuelTypeEnum.C6,
        7: FuelTypeEnum.C7,
        11: FuelTypeEnum.D1,
        12: FuelTypeEnum.D2,
        21: FuelTypeEnum.S1,
        22: FuelTypeEnum.S2,
        23: FuelTypeEnum.S3,
        31: FuelTypeEnum.O1A,
        32: FuelTypeEnum.O1B,
        40: FuelTypeEnum.M1,
        50: FuelTypeEnum.M2,
        70: FuelTypeEnum.M3,
        80: FuelTypeEnum.M4,
    }
)

CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE: Mapping[int, str] = MappingProxyType(
    {
        101: "NF",
        102: "WA",
    }
)
NON_COMBUSTIBLE_FUEL_VALUES = frozenset(CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE)

# national FBP fuel lookup rows for the grid values temporal fuel grids can contain; written
# alongside each temporal fuel grid so consumers can label and colour it.
NATIONAL_FUEL_LOOKUP_COLUMNS = (
    "grid_value",
    "export_value",
    "descriptive_name",
    "fuel_type",
    "r",
    "g",
    "b",
    "h",
    "s",
    "l",
)
NATIONAL_FUEL_LOOKUP: Mapping[int, tuple] = MappingProxyType(
    {
        row[0]: row
        for row in (
            (1, 1, "Spruce-Lichen Woodland", "C-1", 209, 255, 115, 57, 255, 185),
            (2, 2, "Boreal Spruce", "C-2", 34, 102, 51, 95, 128, 68),
            (3, 3, "Mature Jack or Lodgepole Pine", "C-3", 131, 199, 149, 96, 96, 165),
            (4, 4, "Immature Jack or Lodgepole Pine", "C-4", 112, 168, 0, 57, 255, 84),
            (5, 5, "Red and White Pine", "C-5", 223, 184, 230, 206, 122, 207),
            (6, 6, "Conifer Plantation", "C-6", 172, 102, 237, 192, 201, 170),
            (7, 7, "Ponderosa Pine - Douglas-Fir", "C-7", 112, 12, 242, 188, 231, 127),
            (11, 11, "Leafless Aspen", "D-1", 196, 189, 151, 35, 70, 174),
            (12, 12, "Green Aspen (with BUI Thresholding)", "D-2", 137, 112, 68, 27, 86, 103),
            (21, 21, "Jack or Lodgepole Pine Slash", "S-1", 251, 190, 185, 3, 227, 218),
            (22, 22, "White Spruce - Balsam Slash", "S-2", 247, 104, 161, 238, 229, 176),
            (
                23,
                23,
                "Coastal Cedar - Hemlock - Douglas-Fir Slash",
                "S-3",
                174,
                1,
                126,
                225,
                252,
                88,
            ),
            (31, 31, "Matted Grass", "O-1a", 255, 255, 190, 42, 255, 223),
            (32, 32, "Standing Grass", "O-1b", 230, 230, 0, 42, 255, 115),
            (40, 40, "Boreal Mixedwood - Leafless", "M-1", 255, 211, 127, 28, 255, 191),
            (50, 50, "Boreal Mixedwood - Green", "M-2", 255, 170, 0, 28, 255, 128),
            (70, 70, "Dead Balsam Fir Mixedwood - Leafless", "M-3", 99, 0, 0, 0, 255, 50),
            (80, 80, "Dead Balsam Fir Mixedwood - Green", "M-4", 170, 0, 0, 0, 255, 85),
            (101, 101, "Non-fuel", "Non-fuel", 130, 130, 130, 170, 0, 130),
            (102, 102, "Water", "Non-fuel", 115, 223, 255, 138, 255, 185),
        )
    }
)
NODATA_FUEL_TYPE_CODE = -1
PERCENT_CONIFER_GRID_VALUES = frozenset(
    grid_value
    for grid_value, fuel_type in FUEL_TYPES_BY_GRID_VALUE.items()
    if fuel_type in (FuelTypeEnum.M1, FuelTypeEnum.M2)
)
GRASS_FUEL_LOAD = 0.35


def _integer_fuel_values(fuel: np.ndarray) -> set[int]:
    finite_values = fuel[np.isfinite(fuel)]
    non_integral = finite_values[finite_values != np.rint(finite_values)]
    if non_integral.size:
        values = sorted(np.unique(non_integral).tolist())
        raise ValueError(f"Fuel raster contains non-integral classifications: {values}")
    return {int(value) for value in np.unique(finite_values)}


def fuel_type_codes_from_grid(fuel: np.ndarray) -> np.ndarray:
    """Convert a temporal fuel raster (national grid values) into the fuel-type codes used by CFFDRS.

    Every recognized classification, including the non-fuel and water classes, receives its
    matching CFFDRS code. Source nodata pixels receive ``NODATA_FUEL_TYPE_CODE`` so callers can
    keep missing data distinct from valid pixels whose FBP outputs should be zero.

    The returned array has the same shape as ``fuel`` and uses the ``int64`` data type. A
    ``ValueError`` is raised if the source contains a fractional or unknown classification.
    """
    known_values = set(FUEL_TYPES_BY_GRID_VALUE) | set(NON_COMBUSTIBLE_FUEL_VALUES)
    unexpected_values = _integer_fuel_values(fuel) - known_values
    if unexpected_values:
        raise ValueError(
            f"Fuel raster contains unsupported classifications: {sorted(unexpected_values)}"
        )

    fuel_type_codes = np.full(fuel.shape, NODATA_FUEL_TYPE_CODE, dtype=np.int64)
    for grid_value, fuel_type in FUEL_TYPES_BY_GRID_VALUE.items():
        fuel_type_codes[fuel == grid_value] = FUEL_TYPE_CODES[fuel_type.value]
    for grid_value, fuel_type in CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE.items():
        fuel_type_codes[fuel == grid_value] = FUEL_TYPE_CODES[fuel_type]
    return fuel_type_codes
