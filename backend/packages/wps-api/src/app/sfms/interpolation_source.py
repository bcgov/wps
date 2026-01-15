from abc import abstractmethod
from typing import List, Protocol, Tuple

from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.sfms.raster_addresser import SFMSInterpolatedWeatherParameter

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
    """Represents a weather station with temperature and location data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.TEMP

    def adjust_temperature_to_sea_level(self, station_daily: SFMSDailyActual) -> float:
        """
        Adjust station temperature to sea level (0m elevation) using dry adiabatic lapse rate.

        Temperature decreases by 6.5°C per 1000m of elevation gain.
        To adjust to sea level, we ADD temperature based on elevation:
        T_sea_level = T_station + (elevation * lapse_rate)

        :param station: StationTemperature object with elevation and temperature
        :return: Temperature adjusted to sea level in Celsius
        """
        adjustment = station_daily.elevation * LAPSE_RATE
        sea_level_temp = station_daily.temperature + adjustment
        return sea_level_temp

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and sea_level_temp for stations with valid adjusted temperatures.

        :return: Tuple of (lats, lons, values) for stations with valid sea_level_temp
        """
        valid = [
            s
            for s in sfms_actuals
            if s.elevation is not None
            and s.temperature is not None
            and self.adjust_temperature_to_sea_level(s) is not None
        ]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [self.adjust_temperature_to_sea_level(s) for s in valid],
        )


class StationPrecipitationSource(StationInterpolationSource):
    """Represents a weather station with precipitation and location data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.PRECIP

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and precipitation for stations with valid data.

        :param stations: List of StationPrecipitation objects
        :return: Tuple of (lats, lons, values) for stations with valid precipitation
        """
        valid = [s for s in sfms_actuals if s.precipitation is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.precipitation for s in valid],
        )


class StationWindSpeedSource(StationInterpolationSource):
    """Represents a weather station with wind speed and location data for interpolation."""

    def __init__(self):
        super().__init__()
        self.weather_param = SFMSInterpolatedWeatherParameter.WIND_SPEED

    def get_interpolation_data(
        self, sfms_actuals: List[SFMSDailyActual]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and wind speed for stations with valid data.

        :param stations: List of StationWindSpeedSource objects
        :return: Tuple of (lats, lons, values) for stations with valid wind speed
        """
        valid = [s for s in sfms_actuals if s.wind_speed is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.wind_speed for s in valid],
        )
