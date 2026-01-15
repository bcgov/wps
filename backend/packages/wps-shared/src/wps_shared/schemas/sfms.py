"""This module contains pydantic schemas related to SFMS."""

from typing import List, Optional, Tuple
from pydantic import BaseModel


class HourlyTIF(BaseModel):
    """URL of the public hourly tif"""

    url: str


class HourlyTIFs(BaseModel):
    """Encapsulates list of hourly tif urls"""

    hourlies: List[HourlyTIF]


class SFMSDailyActual(BaseModel):
    """Daily Actual"""

    code: int
    lat: float
    lon: float
    elevation: Optional[float] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None


class StationTemperature(BaseModel):
    """Represents a weather station with temperature and location data for interpolation."""

    code: int
    lat: float
    lon: float
    elevation: float
    temperature: float
    sea_level_temp: Optional[float] = None

    @classmethod
    def get_interpolation_data(
        cls, stations: List["StationTemperature"]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and sea_level_temp for stations with valid adjusted temperatures.

        :param stations: List of StationTemperature objects (with sea_level_temp already computed)
        :return: Tuple of (lats, lons, values) for stations with valid sea_level_temp
        """
        valid = [s for s in stations if s.sea_level_temp is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.sea_level_temp for s in valid],
        )


class StationPrecipitation(BaseModel):
    """Represents a weather station with precipitation and location data for interpolation."""

    code: int
    lat: float
    lon: float
    precipitation: float

    @classmethod
    def get_interpolation_data(
        cls, stations: List["StationPrecipitation"]
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract lat, lon, and precipitation for stations with valid data.

        :param stations: List of StationPrecipitation objects
        :return: Tuple of (lats, lons, values) for stations with valid precipitation
        """
        valid = [s for s in stations if s.precipitation is not None]
        return (
            [s.lat for s in valid],
            [s.lon for s in valid],
            [s.precipitation for s in valid],
        )
