"""This module contains pydandict schemas relating to observations (a.k.a. hourlies) for the API."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from wps_shared.schemas.stations import WeatherStation


class WeatherReading(BaseModel):
    """Weather reading for a particular point in time"""

    datetime: Optional[datetime]
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    barometric_pressure: Optional[float] = None
    precipitation: Optional[float] = None
    dewpoint: Optional[float] = None
    ffmc: Optional[float] = None
    isi: Optional[float] = None
    fwi: Optional[float] = None
    observation_valid: Optional[bool] = None
    observation_valid_comment: Optional[str] = None


class WeatherStationHourlyReadings(BaseModel):
    """The weather readings for a particular station"""

    values: List[WeatherReading]
    station: WeatherStation


class WeatherStationHourlyReadingsResponse(BaseModel):
    """Response containing a number of hourly readings."""

    hourlies: List[WeatherStationHourlyReadings]


class HourlyActual(BaseModel):
    """Class representing table structure of 'hourly_actuals.'"""

    weather_date: datetime
    station_code: int
    temp_valid: Optional[bool] = False
    temperature: Optional[float] = None
    dewpoint: Optional[float] = None
    rh_valid: Optional[bool] = False
    relative_humidity: Optional[float]
    wdir_valid: Optional[bool] = False
    wind_direction: Optional[float]
    wspeed_valid: Optional[bool] = False
    wind_speed: Optional[float]
    precip_valid: Optional[bool] = False
    precipitation: Optional[float]
    ffmc: Optional[float]
    isi: Optional[float]
    fwi: Optional[float]
    created_at: Optional[datetime] = datetime.now(tz=timezone.utc)
