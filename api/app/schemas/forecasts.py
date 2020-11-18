""" This module contains pydandict schemas relating to forecasts made by weather forecasters for the API.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class NoonForecastValue(BaseModel):
    """ Data structure for a noon forecast retrieved from BC FireWeather Phase 1 """
    datetime: datetime
    temp_valid: bool
    temperature: int
    rh_valid: bool
    relative_humidity: int
    wdir_valid: bool
    wind_direction: int = None
    wspeed_valid: bool
    wind_speed: float
    precip_valid: bool
    total_precipitation: float
    gc: float = None
    ffmc: float = None
    dmc: float = None
    dc: float = None
    isi: float = None
    bui: float = None
    fwi: float = None
    danger_rating: int = None
    created_at: datetime


class NoonForecast(BaseModel):
    """ Data structure for returning forecasts for a particular station """
    station_code: int
    values: List[NoonForecastValue]


class NoonForecastResponse(BaseModel):
    """ Response containg a number of noon forecasts. """
    noon_forecasts: List[NoonForecast]


class NoonForecastSummaryValues(BaseModel):
    """ Summary of noon forecast values. """
    datetime: datetime
    tmp_min: float
    tmp_max: float
    rh_min: float
    rh_max: float


class NoonForecastSummary(BaseModel):
    """ Summary of noon forecasts for a given station """
    station: WeatherStation
    values: List[NoonForecastSummaryValues] = []


class NoonForecastSummariesResponse(BaseModel):
    """ Response containing noon forecast summaries """
    summaries: List[NoonForecastSummary] = []
