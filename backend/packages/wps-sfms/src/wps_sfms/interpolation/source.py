from abc import abstractmethod
from typing import List, Optional, Protocol, Tuple
import numpy as np

from numpy.typing import NDArray
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.sfms.raster_addresser import SFMSInterpolatedWeatherParameter
from wps_shared.utils.dewpoint import compute_dewpoint

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065


class StationInterpolationSource(Protocol):
    weather_param: SFMSInterpolatedWeatherParameter

    @abstractmethod
    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        raise NotImplementedError


class StationTemperatureSource(StationInterpolationSource):
    """
    Represents a weather station temperature source that owns its station data
    and exposes vectorized computations for sea-level and terrain-adjusted temps.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.TEMP

        self._sfms_actuals = sfms_actuals
        self._lats: Optional[NDArray[np.float32]] = None
        self._lons: Optional[NDArray[np.float32]] = None
        self._elevs: Optional[NDArray[np.float32]] = None
        self._temps: Optional[NDArray[np.float32]] = None
        self._valid_mask: Optional[NDArray[np.float32]] = None

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
        Returns (lats, lons, elevs, temps) as NumPy arrays (float32).
        If only_valid=True, filters out stations missing elevation/temperature.
        """
        self._ensure_arrays()
        if only_valid:
            v = self._valid_mask
            return self._lats[v], self._lons[v], self._elevs[v], self._temps[v]
        return self._lats, self._lons, self._elevs, self._temps

    def get_interpolation_data(
        self, lapse_rate: float = LAPSE_RATE
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """
        Returns arrays for IDW: (lats, lons, sea_level_values), vectorized.
        """
        lats, lons, elevs, temps = self.get_station_arrays(only_valid=True)
        if lats.size == 0:
            # Keep array types stable
            return lats, lons, temps  # all empty arrays

        sea = self.compute_sea_level_temps(temps, elevs, lapse_rate)
        return lats, lons, sea

    @staticmethod
    def compute_sea_level_temps(
        temps: NDArray[np.float32], elevs: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """
        Vectorized: T_sea = T_station + elevation * lapse_rate
        """
        temps = np.asarray(temps, dtype=np.float32)
        elevs = np.asarray(elevs, dtype=np.float32)
        return temps + elevs * np.float32(lapse_rate)

    @staticmethod
    def compute_adjusted_temps(
        sea: NDArray[np.float32], elev: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """
        Vectorized: T(z) = T0 - z * lapse_rate
        """
        sea = np.asarray(sea, dtype=np.float32)
        elev = np.asarray(elev, dtype=np.float32)
        return sea - elev * np.float32(lapse_rate)

    def _ensure_arrays(self) -> None:
        if self._lats is None:
            self._materialize_arrays()

    def _materialize_arrays(self) -> None:
        """
        Pulls values from sfms_actuals into float32 NumPy arrays and computes valid mask.
        """

        # Prefer attribute access; coerce missing/invalid to np.nan
        def get_or_nan(obj, attr):
            val = getattr(obj, attr, None)
            try:
                return np.nan if val is None else float(val)
            except Exception:
                return np.nan

        n = len(self._sfms_actuals)
        self._lats = np.empty(n, dtype=np.float32)
        self._lons = np.empty(n, dtype=np.float32)
        self._elevs = np.empty(n, dtype=np.float32)
        self._temps = np.empty(n, dtype=np.float32)

        for i, s in enumerate(self._sfms_actuals):
            self._lats[i] = get_or_nan(s, "lat")
            self._lons[i] = get_or_nan(s, "lon")
            self._elevs[i] = get_or_nan(s, "elevation")
            self._temps[i] = get_or_nan(s, "temperature")

        self._valid_mask = np.isfinite(self._elevs) & np.isfinite(self._temps)


class StationDewPointSource:
    """
    Represents a weather station dew point source that computes dew point
    from station temperature and relative humidity, then applies lapse rate
    adjustments identically to temperature interpolation.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.RH

        self._sfms_actuals = sfms_actuals
        self._lats: Optional[NDArray[np.float32]] = None
        self._lons: Optional[NDArray[np.float32]] = None
        self._elevs: Optional[NDArray[np.float32]] = None
        self._dewpoints: Optional[NDArray[np.float32]] = None
        self._valid_mask: Optional[NDArray[np.float32]] = None

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
        Returns (lats, lons, elevs, dewpoints) as NumPy arrays (float32).
        If only_valid=True, filters out stations missing elevation/dewpoint.
        """
        self._ensure_arrays()
        if only_valid:
            v = self._valid_mask
            return self._lats[v], self._lons[v], self._elevs[v], self._dewpoints[v]
        return self._lats, self._lons, self._elevs, self._dewpoints

    def get_interpolation_data(
        self, lapse_rate: float = LAPSE_RATE
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """
        Returns arrays for IDW: (lats, lons, sea_level_dewpoints), vectorized.
        Applies the same lapse rate adjustment as temperature.
        """
        lats, lons, elevs, dewpoints = self.get_station_arrays(only_valid=True)
        if lats.size == 0:
            return lats, lons, dewpoints

        sea = StationTemperatureSource.compute_sea_level_temps(dewpoints, elevs, lapse_rate)
        return lats, lons, sea

    def _ensure_arrays(self) -> None:
        if self._lats is None:
            self._materialize_arrays()

    def _materialize_arrays(self) -> None:
        """
        Pulls values from sfms_actuals into float32 NumPy arrays and computes valid mask.
        Dew point is computed from temperature and relative humidity using the legacy formula.
        """

        def get_or_nan(obj, attr):
            val = getattr(obj, attr, None)
            try:
                return np.nan if val is None else float(val)
            except Exception:
                return np.nan

        n = len(self._sfms_actuals)
        self._lats = np.empty(n, dtype=np.float32)
        self._lons = np.empty(n, dtype=np.float32)
        self._elevs = np.empty(n, dtype=np.float32)
        self._dewpoints = np.empty(n, dtype=np.float32)

        for i, s in enumerate(self._sfms_actuals):
            self._lats[i] = get_or_nan(s, "lat")
            self._lons[i] = get_or_nan(s, "lon")
            self._elevs[i] = get_or_nan(s, "elevation")
            td = compute_dewpoint(
                getattr(s, "temperature", None),
                getattr(s, "relative_humidity", None),
            )
            self._dewpoints[i] = np.nan if td is None else float(td)

        self._valid_mask = np.isfinite(self._elevs) & np.isfinite(self._dewpoints)


class StationPrecipitationSource(StationInterpolationSource):
    """Represents a weather station with precipitation and location data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.PRECIP

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and precipitation for daily actuals with valid data.

        :param sfms_actuals: List of SFMSDailyActual objects
        :return: Tuple of (lats, lons, values) for daily actuals with valid precipitation
        """
        valid = [s for s in sfms_actuals if s.precipitation is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.precipitation for s in valid],
        )


class StationFFMCSource(StationInterpolationSource):
    """Represents a weather station with FFMC data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.FFMC

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        valid = [s for s in sfms_actuals if s.ffmc is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.ffmc for s in valid],
        )


class StationDMCSource(StationInterpolationSource):
    """Represents a weather station with DMC data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.DMC

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        valid = [s for s in sfms_actuals if s.dmc is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.dmc for s in valid],
        )


class StationDCSource(StationInterpolationSource):
    """Represents a weather station with DC data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.DC

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        valid = [s for s in sfms_actuals if s.dc is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.dc for s in valid],
        )
