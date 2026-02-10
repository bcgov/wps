from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, Tuple
import numpy as np

from numpy.typing import NDArray
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.sfms.raster_addresser import SFMSInterpolatedWeatherParameter

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065

# Dew point lapse rate: 4.0°C per 1000m based on discussion with JE
DEW_POINT_LAPSE_RATE = 0.004


class StationInterpolationSource(Protocol):
    weather_param: SFMSInterpolatedWeatherParameter

    @abstractmethod
    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        raise NotImplementedError


class LapseRateAdjustedSource(ABC):
    """
    Base class for station sources whose values require lapse-rate elevation
    adjustment (e.g. temperature, dew point).

    Subclasses only need to set ``weather_param`` and implement
    ``_extract_values`` to pull the relevant per-station values from the
    pre-built numpy arrays.
    """

    weather_param: SFMSInterpolatedWeatherParameter

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
        self, lapse_rate: float = DEW_POINT_LAPSE_RATE
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """Returns arrays for IDW: (lats, lons, sea_level_values), vectorized."""
        lats, lons, elevs, values = self.get_station_arrays(only_valid=True)
        if lats.size == 0:
            return lats, lons, values  # all empty arrays

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
        self.weather_param = SFMSInterpolatedWeatherParameter.TEMP

    def _extract_values(self, actuals: List[SFMSDailyActual]) -> NDArray[np.float32]:
        return self._optional_to_array(actuals, "temperature")


class StationDewPointSource(LapseRateAdjustedSource):
    """
    Station source for dew-point values (computed from temperature + RH)
    with lapse-rate elevation adjustment.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        super().__init__(sfms_actuals)
        self.weather_param = SFMSInterpolatedWeatherParameter.RH

    def _extract_values(self, actuals: List[SFMSDailyActual]) -> NDArray[np.float32]:
        temps = self._optional_to_array(actuals, "temperature")
        rhs = self._optional_to_array(actuals, "relative_humidity")
        return self._compute_dewpoint(temps, rhs)

    @staticmethod
    def _compute_dewpoint(
        temp: NDArray[np.float32], rh: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        """Vectorized dewpoint from temperature (°C) and relative humidity (%).

        Uses the simple approximation: Td = T - (100 - RH) / 5
        """
        return (temp - (100.0 - rh) / 5.0).astype(np.float32)

    @staticmethod
    def compute_rh(temp: np.ndarray, dewpoint: np.ndarray) -> np.ndarray:
        """
        Compute relative humidity from temperature and dew point.

        Uses the simple approximation: RH = 100 - 5 * (T - Td)

        :param temp: Temperature array in Celsius
        :param dewpoint: Dew point temperature array in Celsius
        :return: Relative humidity as percentage (0-100), clamped
        """
        rh = 100.0 - 5.0 * (temp - dewpoint)
        return np.clip(rh, 0.0, 100.0).astype(np.float32)


class StationActualSource(StationInterpolationSource):
    """Generic source for interpolating a named attribute from SFMSDailyActual."""

    # Map enum values to SFMSDailyActual attribute names where they differ
    _ATTRIBUTE_OVERRIDES = {
        SFMSInterpolatedWeatherParameter.PRECIP: "precipitation",
    }

    def __init__(self, weather_param: SFMSInterpolatedWeatherParameter):
        super().__init__()
        self.weather_param = weather_param
        self._attribute = self._ATTRIBUTE_OVERRIDES.get(weather_param, weather_param.value)

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        valid = [s for s in sfms_actuals if getattr(s, self._attribute) is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [getattr(s, self._attribute) for s in valid],
        )


def StationPrecipitationSource() -> StationActualSource:
    return StationActualSource(SFMSInterpolatedWeatherParameter.PRECIP)


def StationFFMCSource() -> StationActualSource:
    return StationActualSource(SFMSInterpolatedWeatherParameter.FFMC)


def StationDMCSource() -> StationActualSource:
    return StationActualSource(SFMSInterpolatedWeatherParameter.DMC)


def StationDCSource() -> StationActualSource:
    return StationActualSource(SFMSInterpolatedWeatherParameter.DC)
