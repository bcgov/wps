""" This module contains pydantic schemas relating to forecasts made by weather forecasters for the API.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class NoonForecastValue(BaseModel):
    """ Data structure for a noon forecast retrieved from BC FireWeather Phase 1 """
    datetime: datetime
    temp_valid: bool
    temperature: Optional[int] = None
    rh_valid: bool
    relative_humidity: Optional[int] = None
    wdir_valid: bool
    wind_direction: Optional[int] = None
    wspeed_valid: bool
    wind_speed: float
    precip_valid: bool
    total_precipitation: float
    gc: Optional[float] = None
    ffmc: Optional[float] = None
    dmc: Optional[float] = None
    dc: Optional[float] = None
    isi: Optional[float] = None
    bui: Optional[float] = None
    fwi: Optional[float] = None
    danger_rating: Optional[int] = None
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
