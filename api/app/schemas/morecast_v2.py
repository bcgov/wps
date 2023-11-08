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
    NAM = 'NAM'
    MANUAL = 'MANUAL'
    RDPS = 'RDPS'


class WeatherDeterminate(str, Enum):
    """ Enumerator for all valid determinate weather sources"""
    GDPS = 'GDPS'
    GDPS_BIAS = 'GDPS_BIAS'
    GFS = 'GFS'
    GFS_BIAS = 'GFS_BIAS'
    HRDPS = 'HRDPS'
    HRDPS_BIAS = 'HRDPS_BIAS'
    NAM = 'NAM'
    NAM_BIAS = 'NAM_BIAS'
    RDPS = 'RDPS'
    RDPS_BIAS = 'RDPS_BIAS'

    # non prediction models
    FORECAST = 'Forecast'
    ACTUAL = 'Actual'


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


class MoreCastForecastInput(BaseModel):
    """ Forecasted daily request """
    station_code: int
    for_date: int
    temp: float
    rh: float
    precip: float
    wind_speed: float
    wind_direction: int | None = None


class MoreCastForecastRequest(BaseModel):
    """ Incoming daily forecasts to be saved """
    token: str  # WF1 token
    forecasts: List[MoreCastForecastInput]


class MoreCastForecastOutput(MoreCastForecastInput):
    """ Outgoing forecast daily response item """
    update_timestamp: int


class MorecastForecastResponse(BaseModel):
    """ Outgoing forecast daily response """
    forecasts: List[MoreCastForecastOutput]


class ObservedDailiesForStations(BaseModel):
    """ Request for observed dailies for stations """
    station_codes: List[int]


class StationDailyFromWF1(BaseModel):
    """ Daily weather data (forecast or observed) for a specific station and date retrieved from WF1 API """
    created_by: str
    forecast_id: str
    station_code: int
    station_name: str
    utcTimestamp: datetime
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None


class StationDailiesResponse(BaseModel):
    """ List of StationDailyFromWF1 records as response """
    dailies: List[StationDailyFromWF1]


class WeatherIndeterminate(BaseModel):
    """ Used to represent a predicted or actual value """
    station_code: int
    station_name: str
    determinate: WeatherDeterminate
    utc_timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None
    fine_fuel_moisture_code: Optional[float] = None
    duff_moisture_code: Optional[float] = None
    drought_code: Optional[float] = None
    initial_spread_index: Optional[float] = None
    build_up_index: Optional[float] = None
    fire_weather_index: Optional[float] = None
    danger_rating: Optional[int] = None


class IndeterminateDailiesResponse(BaseModel):
    actuals: List[WeatherIndeterminate]
    predictions: List[WeatherIndeterminate]
    forecasts: List[WeatherIndeterminate]


class SimulateIndeterminateIndices(BaseModel):
    simulate_records: List[WeatherIndeterminate]


class SimulatedWeatherIndeterminateResponse(BaseModel):
    simulated_forecasts: List[WeatherIndeterminate]


class WF1ForecastRecordType(BaseModel):
    id: str = "FORECAST"
    displayLabel: str = "Forecast"


class WF1PostForecast(BaseModel):
    """ Used to represent a forecast to be POSTed to WF1 """
    archive: str = 'false'
    createdBy: Optional[str] = None
    id: Optional[str] = None
    station: str  # station URL
    stationId: str  # station UUID
    weatherTimestamp: int  # UTC timestamp in millis
    temperature: float
    relativeHumidity: float
    precipitation: float
    windSpeed: float
    windDirection: Optional[float] = None
    recordType: WF1ForecastRecordType
