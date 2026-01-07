"""This module contains pydantic models for Morecast v2"""

from enum import Enum
from typing import List

from pydantic import BaseModel
from wps_wf1.models import StationDailyFromWF1, WeatherIndeterminate


class ModelChoice(str, Enum):
    """Enumerator for all valid forecasted value types"""

    GDPS = "GDPS"
    GFS = "GFS"
    HRDPS = "HRDPS"
    NAM = "NAM"
    MANUAL = "MANUAL"
    RDPS = "RDPS"


class ForecastedTemperature(BaseModel):
    """Forecaster chosen temperature"""

    temp: float
    choice: ModelChoice


class ForecastedRH(BaseModel):
    """Forecaster chosen rh"""

    rh: float
    choice: ModelChoice


class ForecastedPrecip(BaseModel):
    """Forecaster chosen 24-hour precipitation mm"""

    precip: float
    choice: ModelChoice


class ForecastedWindSpeed(BaseModel):
    """Forecaster chosen wind speed"""

    wind_speed: float
    choice: ModelChoice


class ForecastedWindDirection(BaseModel):
    """Forecaster chosen wind direction"""

    wind_direction: float
    choice: ModelChoice


class MoreCastForecastInput(BaseModel):
    """Forecasted daily request"""

    station_code: int
    for_date: int
    temp: float
    rh: float
    precip: float
    wind_speed: float
    wind_direction: int | None = None
    grass_curing: float | None = None


class MoreCastForecastRequest(BaseModel):
    """Incoming daily forecasts to be saved"""

    forecasts: List[MoreCastForecastInput]


class MoreCastForecastOutput(MoreCastForecastInput):
    """Outgoing forecast daily response item"""

    update_timestamp: int


class MorecastForecastResponse(BaseModel):
    """Outgoing forecast daily response"""

    forecasts: List[MoreCastForecastOutput]


class ObservedDailiesForStations(BaseModel):
    """Request for observed dailies for stations"""

    station_codes: List[int]


class StationDailiesResponse(BaseModel):
    """List of StationDailyFromWF1 records as response"""

    dailies: List[StationDailyFromWF1]


class IndeterminateDailiesResponse(BaseModel):
    actuals: List[WeatherIndeterminate]
    forecasts: List[WeatherIndeterminate]
    grass_curing: List[WeatherIndeterminate]
    predictions: List[WeatherIndeterminate]
