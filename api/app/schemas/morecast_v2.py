""" This module contains pydantic models for Morecast v2"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ModelChoice(str, Enum):
    """ Enumerator for all valid forecasted value types """
    GDPS = 'GDPS'
    GFS = 'GFS'
    HRDPS = 'HRDPS'
    RDPS = 'RDPS'
    MANUAL = 'MANUAL'


class ForecastedTemperature(BaseModel):
    """ Forecaster chosen temperature """
    temp: float
    choice: ModelChoice


class ForecastedRH(BaseModel):
    """ Forecaster chosen rh """
    rh: float
    choice: ModelChoice


class ForecastedPrecip(BaseModel):
    """ Forecaster chosen 24-hour precipitation mm """
    precip: float
    choice: ModelChoice


class ForecastedWindSpeed(BaseModel):
    """ Forecaster chosen wind speed """
    wind_speed: float
    choice: ModelChoice


class ForecastedWindDirection(BaseModel):
    """ Forecaster chosen wind direction """
    wind_direction: float
    choice: ModelChoice


class MorecastForecastRequest(BaseModel):
    """ Forecasted daily request """
    station_code: int
    for_date: int
    temp: ForecastedTemperature
    rh: ForecastedRH
    precip: ForecastedPrecip
    wind_speed: ForecastedWindSpeed
    wind_direction: ForecastedWindDirection


class MorecastForecastResponse(MorecastForecastRequest):
    """ Forecasted daily response """
    update_timestamp: int


class YesterdayStationDailies(BaseModel):
    """ Yesterday station dailies request """
    station_codes: List[int]


class YesterdayDaily(BaseModel):
    """ Yesterday station daily data """
    station_code: int
    station_name: str
    utcTimestamp: datetime
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None


class YesterdayStationDailiesResponse(BaseModel):
    """ Yesterday station dailies response """
    dailies: List[YesterdayDaily]
