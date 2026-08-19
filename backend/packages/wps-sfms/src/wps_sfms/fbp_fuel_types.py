"""Fuel-grid classifications used by SFMS fire behaviour calculations."""

from types import MappingProxyType
from typing import Mapping

import numpy as np
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.fuel_types import FuelTypeEnum

# base types are used outside the greenup/standing period and by calculations such as SFC that
# deliberately do not apply seasonal variants.
FUEL_TYPES_BY_GRID_VALUE: Mapping[int, FuelTypeEnum] = MappingProxyType(
    {
        1: FuelTypeEnum.C1,
        2: FuelTypeEnum.C2,
        3: FuelTypeEnum.C3,
        4: FuelTypeEnum.C4,
        5: FuelTypeEnum.C5,
        6: FuelTypeEnum.C6,
        7: FuelTypeEnum.C7,
        8: FuelTypeEnum.D1,
        9: FuelTypeEnum.S1,
        10: FuelTypeEnum.S2,
        11: FuelTypeEnum.S3,
        12: FuelTypeEnum.O1A,
        13: FuelTypeEnum.M3,
        14: FuelTypeEnum.M1,
    }
)

# seasonal overrides are applied by future FBP calculations during the configured
# greenup/standing period.
SEASONAL_FUEL_TYPE_OVERRIDES: Mapping[int, FuelTypeEnum] = MappingProxyType(
    {
        8: FuelTypeEnum.D2,
        12: FuelTypeEnum.O1B,
        13: FuelTypeEnum.M4,
        14: FuelTypeEnum.M2,
    }
)

CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE: Mapping[int, str] = MappingProxyType(
    {
        99: "NF",
        102: "WA",
    }
)
NON_COMBUSTIBLE_FUEL_VALUES = frozenset(CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE)
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
    """Convert an SFMS fuel raster into the fuel-type codes used by CFFDRS.

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
