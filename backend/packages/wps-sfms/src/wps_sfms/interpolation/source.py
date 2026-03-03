from abc import ABC, abstractmethod
import logging
from typing import List, Optional, Protocol, Tuple, runtime_checkable
import numpy as np

from numpy.typing import NDArray
from wps_shared.schemas.sfms import SFMSDailyActual

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065

# Dew point lapse rate: 2.0°C per 1000m: https://www.atmos.illinois.edu/~snodgrss/Airflow_over_mtn.html
DEW_POINT_LAPSE_RATE = 0.002


@runtime_checkable
class StationInterpolationSource(Protocol):
    def get_interpolation_data(self) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]: ...


class LapseRateAdjustedSource(ABC):
    """
    Base class for station sources whose values require lapse-rate elevation
    adjustment (e.g. temperature, dew point).

    Subclasses only need to implement ``_extract_values`` to pull the relevant
    per-station values from the pre-built numpy arrays.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        self._sfms_actuals = sfms_actuals
        self._lats: Optional[NDArray[np.float32]] = None
        self._lons: Optional[NDArray[np.float32]] = None
        self._elevs: Optional[NDArray[np.float32]] = None
        self._values: Optional[NDArray[np.float32]] = None
        self._valid_mask: Optional[NDArray[np.float32]] = None

    @abstractmethod
    def _extract_values(self, actuals: List[SFMSDailyActual]) -> NDArray[np.float32]:
        """Return a float32 array of values (one per station), ``np.nan`` where unavailable."""
        ...

    @staticmethod
    def compute_sea_level_values(
        values: NDArray[np.float32], elevs: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """Vectorized: V_sea = V_station + elevation * lapse_rate"""
        values = np.asarray(values, dtype=np.float32)
        elevs = np.asarray(elevs, dtype=np.float32)
        return values + elevs * np.float32(lapse_rate)

    @staticmethod
    def compute_adjusted_values(
        sea: NDArray[np.float32], elev: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """Vectorized: V(z) = V_sea - z * lapse_rate"""
        sea = np.asarray(sea, dtype=np.float32)
        elev = np.asarray(elev, dtype=np.float32)
        return sea - elev * np.float32(lapse_rate)

    def get_station_count(self) -> int:
        return len(self._sfms_actuals)

    def get_station_arrays(
        self, only_valid: bool = True
    ) -> Tuple[
        NDArray[np.float32],
        NDArray[np.float32],
        NDArray[np.float32],
        NDArray[np.float32],
    ]:
        """
        Returns (lats, lons, elevs, values) as NumPy arrays (float32).
        If only_valid=True, filters out stations missing elevation or value.
        """
        self._ensure_arrays()
        if only_valid:
            v = self._valid_mask
            return self._lats[v], self._lons[v], self._elevs[v], self._values[v]
        return self._lats, self._lons, self._elevs, self._values

    def get_interpolation_data(
        self, lapse_rate: float = LAPSE_RATE
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """Returns arrays for IDW: (lats, lons, sea_level_values), vectorized."""
        lats, lons, elevs, values = self.get_station_arrays(only_valid=True)
        if lats.size == 0:
            logger.warning(
                "%s has no valid stations (missing elevation or value) — interpolation will produce no output",
                type(self).__name__,
            )
            return lats, lons, values

        sea = self.compute_sea_level_values(values, elevs, lapse_rate)
        return lats, lons, sea

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_arrays(self) -> None:
        if self._lats is None:
            self._materialize_arrays()

    @staticmethod
    def _optional_to_array(actuals: List[SFMSDailyActual], attr: str) -> NDArray[np.float32]:
        """Extract an optional float attribute from each actual into a float32 array (None → nan)."""
        return np.array(
            [getattr(a, attr) if getattr(a, attr) is not None else np.nan for a in actuals],
            dtype=np.float32,
        )

    def _materialize_arrays(self) -> None:
        """Pulls values from sfms_actuals into float32 NumPy arrays and computes valid mask."""
        actuals = self._sfms_actuals
        self._lats = np.array([a.lat for a in actuals], dtype=np.float32)
        self._lons = np.array([a.lon for a in actuals], dtype=np.float32)
        self._elevs = self._optional_to_array(actuals, "elevation")
        self._values = self._extract_values(actuals)
        self._valid_mask = np.isfinite(self._elevs) & np.isfinite(self._values)


class StationTemperatureSource(LapseRateAdjustedSource):
    """Station source for temperature values with lapse-rate elevation adjustment."""

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        super().__init__(sfms_actuals)

    def _extract_values(self, actuals: List[SFMSDailyActual]) -> NDArray[np.float32]:
        return self._optional_to_array(actuals, "temperature")


class StationDewPointSource(LapseRateAdjustedSource):
    """
    Station source for dew-point values (computed from temperature + RH)
    with lapse-rate elevation adjustment.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        super().__init__(sfms_actuals)

    def _extract_values(self, actuals: List[SFMSDailyActual]) -> NDArray[np.float32]:
        dewpoints = self._optional_to_array(actuals, "dewpoint")
        return dewpoints

    @staticmethod
    def compute_rh(temp: np.ndarray, dewpoint: np.ndarray) -> np.ndarray:
        """
        Compute relative humidity from temperature and dew point using the Arden Buck equation.

        Buck (1981): e_s(T) = 6.1121 * exp((18.678 - T/234.5) * (T / (257.14 + T)))
        RH = 100 * e_s(Td) / e_s(T)

        :param temp: Temperature array in Celsius
        :param dewpoint: Dew point temperature array in Celsius
        :return: Relative humidity as percentage (0-100), clamped
        """
        e_td = 6.1121 * np.exp((18.678 - dewpoint / 234.5) * (dewpoint / (257.14 + dewpoint)))
        e_t = 6.1121 * np.exp((18.678 - temp / 234.5) * (temp / (257.14 + temp)))
        rh = 100.0 * e_td / e_t
        return np.clip(rh, 0.0, 100.0).astype(np.float32)


_VALID_SFMS_ATTRIBUTES = frozenset(SFMSDailyActual.model_fields.keys())


class StationActualSource(StationInterpolationSource):
    """Generic source for interpolating a named attribute from SFMSDailyActual."""

    def __init__(self, attribute: str, sfms_actuals: List[SFMSDailyActual]):
        if attribute not in _VALID_SFMS_ATTRIBUTES:
            raise ValueError(f"Unknown attribute {attribute!r} on SFMSDailyActual. Valid attributes: {sorted(_VALID_SFMS_ATTRIBUTES)}")
        self._attribute = attribute
        self._sfms_actuals = sfms_actuals

    def get_interpolation_data(self) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        valid = [s for s in self._sfms_actuals if getattr(s, self._attribute) is not None]
        return (
            np.array([s.lat for s in valid], dtype=np.float32),
            np.array([s.lon for s in valid], dtype=np.float32),
            np.array([getattr(s, self._attribute) for s in valid], dtype=np.float32),
        )


def StationPrecipitationSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("precipitation", sfms_actuals)


def StationFFMCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("ffmc", sfms_actuals)


def StationDMCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("dmc", sfms_actuals)


def StationDCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("dc", sfms_actuals)
