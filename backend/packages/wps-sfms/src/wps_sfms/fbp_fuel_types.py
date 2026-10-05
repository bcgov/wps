"""Fuel-grid classifications used by SFMS fire behaviour calculations."""

from collections.abc import Mapping, Set
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.schemas.sfms import FuelCodesLookup

NODATA_FUEL_TYPE_CODE = -1
NON_FUEL_TYPE = "NF"
PERCENT_CONIFER_FUEL_TYPES = frozenset({"M1", "M2"})
GRASS_FUEL_LOAD = 0.35


def _integer_fuel_values(fuel: np.ndarray) -> set[int]:
    finite_values = fuel[np.isfinite(fuel)]
    non_integral = finite_values[finite_values != np.rint(finite_values)]
    if non_integral.size:
        values = sorted(np.unique(non_integral).tolist())
        raise ValueError(f"Fuel raster contains non-integral classifications: {values}")
    return {int(value) for value in np.unique(finite_values)}


@dataclass(frozen=True)
class CFFDRSFuelTypes:
    """CFFDRS fuel type for each grid value of a fuel grid, e.g. ``{12: "D2", 101: "NF"}``."""

    by_grid_value: Mapping[int, str]

    @classmethod
    def from_lookup(cls, lookup: FuelCodesLookup) -> "CFFDRSFuelTypes":
        """Read the CFFDRS fuel types from a fuel grid's fuel codes lookup.

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
        return cls(MappingProxyType(fuel_types))

    def cffdrs_codes(self, fuel: np.ndarray) -> np.ndarray:
        """Convert a fuel raster into the fuel-type codes used by CFFDRS.

        Source nodata pixels receive ``NODATA_FUEL_TYPE_CODE`` so callers can keep missing data
        distinct from valid pixels whose FBP outputs should be zero.

        The returned array has the same shape as ``fuel`` and uses the ``int64`` data type. A
        ``ValueError`` is raised if the source contains a fractional or unknown classification.
        """
        unexpected_values = _integer_fuel_values(fuel) - set(self.by_grid_value)
        if unexpected_values:
            raise ValueError(
                f"Fuel raster contains unsupported classifications: {sorted(unexpected_values)}"
            )

        fuel_type_codes = np.full(fuel.shape, NODATA_FUEL_TYPE_CODE, dtype=np.int64)
        for grid_value, fuel_type in self.by_grid_value.items():
            fuel_type_codes[fuel == grid_value] = FUEL_TYPE_CODES[fuel_type]
        return fuel_type_codes

    def non_combustible_mask(self, fuel: np.ndarray) -> np.ndarray:
        """Return where ``fuel`` is a non-fuel classification, including water."""
        return self._mask(fuel, {NON_FUEL_TYPE})

    def mixedwood_mask(self, fuel: np.ndarray) -> np.ndarray:
        """Return where ``fuel`` is M1 or M2, the fuel types that need percent conifer."""
        return self._mask(fuel, PERCENT_CONIFER_FUEL_TYPES)

    def _mask(self, fuel: np.ndarray, fuel_types: Set[str]) -> np.ndarray:
        grid_values = [value for value, ft in self.by_grid_value.items() if ft in fuel_types]
        return np.isin(fuel, grid_values)
