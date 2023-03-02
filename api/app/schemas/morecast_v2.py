""" This module contains pydantic models for Morecast v2"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


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


class YesterdayObservationStations(BaseModel):
    """ Yesterday station observation request """
    station_codes: List[int]


class YesterdayDaily(BaseModel):
    temperature: Optional[float] = None
    status: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None


class YesterdayObservationStationsResponse(BaseModel):
    observations: List[YesterdayDaily]
