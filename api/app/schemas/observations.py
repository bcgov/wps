""" This module contains pydandict schemas relating to observations (a.k.a. hourlies) for the API.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class WeatherReading(BaseModel):
    """ Weather reading for a particular point in time """
    datetime: datetime
    temperature: float = None
    relative_humidity: float = None
    wind_speed: float = None
    wind_direction: float = None
    barometric_pressure: float = None
    precipitation: float = None
    dewpoint: float = None
    ffmc: float = None
    isi: float = None
    fwi: float = None
    observation_valid_ind: bool = None
    observation_valid_comment: str = None


class WeatherStationHourlyReadings(BaseModel):
    """ The weather readings for a particular station """
    values: List[WeatherReading]
    station: WeatherStation


class WeatherStationHourlyReadingsResponse(BaseModel):
    """ Response containing a number of hourly readings. """
    hourlies: List[WeatherStationHourlyReadings]
