""" This module contains pydandict schemas relating to observations (a.k.a. hourlies) for the API.
"""
from datetime import datetime
from typing import List, Union
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class WeatherReading(BaseModel):
    """ Weather reading for a particular point in time """
    datetime: Union[datetime, None]
    temperature: Union[float, None] = None
    relative_humidity: Union[float, None] = None
    wind_speed: Union[float, None] = None
    wind_direction: Union[float, None] = None
    barometric_pressure: Union[float, None] = None
    precipitation: Union[float, None] = None
    dewpoint: Union[float, None] = None
    ffmc: Union[float, None] = None
    isi: Union[float, None] = None
    fwi: Union[float, None] = None
    observation_valid: Union[bool, None] = None
    observation_valid_comment: Union[str, None] = None


class WeatherStationHourlyReadings(BaseModel):
    """ The weather readings for a particular station """
    values: List[WeatherReading]
    station: WeatherStation


class WeatherStationHourlyReadingsResponse(BaseModel):
    """ Response containing a number of hourly readings. """
    hourlies: List[WeatherStationHourlyReadings]
