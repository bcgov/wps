"""Fuel-grid classifications used by SFMS fire behaviour calculations."""

from types import MappingProxyType
from typing import Mapping

import numpy as np
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.schemas.sfms import FuelCode, FuelCodesLookup

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

# national FBP fuel lookup rows for the grid values temporal fuel grids can contain; written
# alongside each temporal fuel grid so consumers can label and colour it.
NATIONAL_FUEL_LOOKUP: Mapping[int, FuelCode] = MappingProxyType(
    {
        row[0]: FuelCode(**dict(zip(FuelCode.model_fields, row)))
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
NON_FUEL_TYPE = "NF"
PERCENT_CONIFER_FUEL_TYPES = frozenset({"M1", "M2"})
GRASS_FUEL_LOAD = 0.35


def cffdrs_fuel_types_from_lookup(lookup: FuelCodesLookup) -> dict[int, str]:
    """Map each fuel codes lookup row's grid value to its CFFDRS fuel type, e.g. ``{12: "D2"}``.

    National lookup labels such as ``"O-1a"`` become CFFDRS fuel types such as ``"O1A"``, and
    every ``"Non-fuel"`` row (including water) becomes ``"NF"``. A ``ValueError`` is raised for
    labels CFFDRS cannot calculate, such as the combined seasonal class ``"M-1/M-2"``.
    """
    fuel_types = {}
    for row in lookup.root:
        label = row.fuel_type
        fuel_type = NON_FUEL_TYPE if label == "Non-fuel" else label.replace("-", "").upper()
        if fuel_type not in FUEL_TYPE_CODES:
            raise ValueError(
                f"Fuel lookup contains unsupported fuel type {label!r} "
                f"for grid value {row.grid_value}"
            )
        fuel_types[row.grid_value] = fuel_type
    return fuel_types


def _integer_fuel_values(fuel: np.ndarray) -> set[int]:
    finite_values = fuel[np.isfinite(fuel)]
    non_integral = finite_values[finite_values != np.rint(finite_values)]
    if non_integral.size:
        values = sorted(np.unique(non_integral).tolist())
        raise ValueError(f"Fuel raster contains non-integral classifications: {values}")
    return {int(value) for value in np.unique(finite_values)}


def fuel_type_codes_from_grid(fuel: np.ndarray, fuel_types: Mapping[int, str]) -> np.ndarray:
    """Convert a fuel raster into the fuel-type codes used by CFFDRS.

    ``fuel_types`` maps each grid value to its CFFDRS fuel type (see
    ``cffdrs_fuel_types_from_lookup``). Source nodata pixels receive ``NODATA_FUEL_TYPE_CODE`` so
    callers can keep missing data distinct from valid pixels whose FBP outputs should be zero.

    The returned array has the same shape as ``fuel`` and uses the ``int64`` data type. A
    ``ValueError`` is raised if the source contains a fractional or unknown classification.
    """
    unexpected_values = _integer_fuel_values(fuel) - set(fuel_types)
    if unexpected_values:
        raise ValueError(
            f"Fuel raster contains unsupported classifications: {sorted(unexpected_values)}"
        )

    fuel_type_codes = np.full(fuel.shape, NODATA_FUEL_TYPE_CODE, dtype=np.int64)
    for grid_value, fuel_type in fuel_types.items():
        fuel_type_codes[fuel == grid_value] = FUEL_TYPE_CODES[fuel_type]
    return fuel_type_codes
