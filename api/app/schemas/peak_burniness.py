""" This module contains pydandict schemas relating to the percentile calculator for the API.
"""
from typing import List, Dict
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class PeakValuesRequest(BaseModel):
    """ A request for a given set of stations. """
    stations: List[int]


class StationSummary(BaseModel):
    """ The summary of daily weather data for a given station. """
    max_temp: float = None
    min_rh: int = None
    max_wind_speed: float = None
    max_ffmc: float = None
    max_fwi: float = None
    hour_max_temp: int = None
    hour_min_rh: int = None
    hour_max_wind_speed: int = None
    hour_max_ffmc: int = None
    hour_max_fwi: int = None
    week: str = None


class CalculatedResponse(BaseModel):
    """ The combined response for a set of stations. """
    stations: Dict[int, List[StationSummary]] = {}
