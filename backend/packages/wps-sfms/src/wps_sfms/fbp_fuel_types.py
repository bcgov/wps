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
        fuel_code.grid_value: fuel_code
        for fuel_code in (
            FuelCode(
                grid_value=1,
                export_value=1,
                descriptive_name="Spruce-Lichen Woodland",
                fuel_type="C-1",
                r=209,
                g=255,
                b=115,
                h=57,
                s=255,
                l=185,
            ),
            FuelCode(
                grid_value=2,
                export_value=2,
                descriptive_name="Boreal Spruce",
                fuel_type="C-2",
                r=34,
                g=102,
                b=51,
                h=95,
                s=128,
                l=68,
            ),
            FuelCode(
                grid_value=3,
                export_value=3,
                descriptive_name="Mature Jack or Lodgepole Pine",
                fuel_type="C-3",
                r=131,
                g=199,
                b=149,
                h=96,
                s=96,
                l=165,
            ),
            FuelCode(
                grid_value=4,
                export_value=4,
                descriptive_name="Immature Jack or Lodgepole Pine",
                fuel_type="C-4",
                r=112,
                g=168,
                b=0,
                h=57,
                s=255,
                l=84,
            ),
            FuelCode(
                grid_value=5,
                export_value=5,
                descriptive_name="Red and White Pine",
                fuel_type="C-5",
                r=223,
                g=184,
                b=230,
                h=206,
                s=122,
                l=207,
            ),
            FuelCode(
                grid_value=6,
                export_value=6,
                descriptive_name="Conifer Plantation",
                fuel_type="C-6",
                r=172,
                g=102,
                b=237,
                h=192,
                s=201,
                l=170,
            ),
            FuelCode(
                grid_value=7,
                export_value=7,
                descriptive_name="Ponderosa Pine - Douglas-Fir",
                fuel_type="C-7",
                r=112,
                g=12,
                b=242,
                h=188,
                s=231,
                l=127,
            ),
            FuelCode(
                grid_value=11,
                export_value=11,
                descriptive_name="Leafless Aspen",
                fuel_type="D-1",
                r=196,
                g=189,
                b=151,
                h=35,
                s=70,
                l=174,
            ),
            FuelCode(
                grid_value=12,
                export_value=12,
                descriptive_name="Green Aspen (with BUI Thresholding)",
                fuel_type="D-2",
                r=137,
                g=112,
                b=68,
                h=27,
                s=86,
                l=103,
            ),
            FuelCode(
                grid_value=21,
                export_value=21,
                descriptive_name="Jack or Lodgepole Pine Slash",
                fuel_type="S-1",
                r=251,
                g=190,
                b=185,
                h=3,
                s=227,
                l=218,
            ),
            FuelCode(
                grid_value=22,
                export_value=22,
                descriptive_name="White Spruce - Balsam Slash",
                fuel_type="S-2",
                r=247,
                g=104,
                b=161,
                h=238,
                s=229,
                l=176,
            ),
            FuelCode(
                grid_value=23,
                export_value=23,
                descriptive_name="Coastal Cedar - Hemlock - Douglas-Fir Slash",
                fuel_type="S-3",
                r=174,
                g=1,
                b=126,
                h=225,
                s=252,
                l=88,
            ),
            FuelCode(
                grid_value=31,
                export_value=31,
                descriptive_name="Matted Grass",
                fuel_type="O-1a",
                r=255,
                g=255,
                b=190,
                h=42,
                s=255,
                l=223,
            ),
            FuelCode(
                grid_value=32,
                export_value=32,
                descriptive_name="Standing Grass",
                fuel_type="O-1b",
                r=230,
                g=230,
                b=0,
                h=42,
                s=255,
                l=115,
            ),
            FuelCode(
                grid_value=40,
                export_value=40,
                descriptive_name="Boreal Mixedwood - Leafless",
                fuel_type="M-1",
                r=255,
                g=211,
                b=127,
                h=28,
                s=255,
                l=191,
            ),
            FuelCode(
                grid_value=50,
                export_value=50,
                descriptive_name="Boreal Mixedwood - Green",
                fuel_type="M-2",
                r=255,
                g=170,
                b=0,
                h=28,
                s=255,
                l=128,
            ),
            FuelCode(
                grid_value=70,
                export_value=70,
                descriptive_name="Dead Balsam Fir Mixedwood - Leafless",
                fuel_type="M-3",
                r=99,
                g=0,
                b=0,
                h=0,
                s=255,
                l=50,
            ),
            FuelCode(
                grid_value=80,
                export_value=80,
                descriptive_name="Dead Balsam Fir Mixedwood - Green",
                fuel_type="M-4",
                r=170,
                g=0,
                b=0,
                h=0,
                s=255,
                l=85,
            ),
            FuelCode(
                grid_value=101,
                export_value=101,
                descriptive_name="Non-fuel",
                fuel_type="Non-fuel",
                r=130,
                g=130,
                b=130,
                h=170,
                s=0,
                l=130,
            ),
            FuelCode(
                grid_value=102,
                export_value=102,
                descriptive_name="Water",
                fuel_type="Non-fuel",
                r=115,
                g=223,
                b=255,
                h=138,
                s=255,
                l=185,
            ),
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
