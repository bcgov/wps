""" This module contains pydandict schemas relating to observations (a.k.a. hourlies) for the API.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class WeatherReading(BaseModel):
    """ Weather reading for a particular point in time """
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
    """ The weather readings for a particular station """
    values: List[WeatherReading]
    station: WeatherStation


class WeatherStationHourlyReadingsResponse(BaseModel):
    """ Response containing a number of hourly readings. """
    hourlies: List[WeatherStationHourlyReadings]
