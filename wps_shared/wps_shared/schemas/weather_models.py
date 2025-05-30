"""This module contains pydandict schemas relating to weather models for the API."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from wps_shared.schemas.stations import WeatherStation


class WeatherPredictionModel(BaseModel):
    """The full name & acronym for a weather prediction model"""

    name: str
    abbrev: str


class CHainesModelRunPredictions(BaseModel):
    """List of predictions"""

    model: WeatherPredictionModel
    model_run_timestamp: datetime
    prediction_timestamps: List[datetime]


class CHainesModelRuns(BaseModel):
    """List of model run timestamps"""

    model_runs: List[CHainesModelRunPredictions]


class CHainesRequest(BaseModel):
    """Request for particular model run"""

    model_run_timestamp: datetime
    prediction_timestamp: datetime


class WeatherModelPredictionSummaryValues(BaseModel):
    """Summary of model prediction values."""

    datetime: datetime
    tmp_tgl_2_5th: float
    tmp_tgl_2_90th: float
    tmp_tgl_2_median: float
    rh_tgl_2_5th: float
    rh_tgl_2_90th: float
    rh_tgl_2_median: float


class WeatherModelPredictionSummary(BaseModel):
    """Summary of weather predictions for a given model.
    Detail: For the global model, we end up with 20 different predictions for every three hours of any given
    day, this represents a summary of that data."""

    station: WeatherStation
    model: WeatherPredictionModel
    values: List[WeatherModelPredictionSummaryValues] = []


class WeatherModelPredictionSummaryResponse(BaseModel):
    """Response containing prediction summaries for a given weather model."""

    summaries: List[WeatherModelPredictionSummary]


class BaseWeatherPredictionValues(BaseModel):
    """The predicted weather values."""

    datetime: datetime
    temperature: Optional[float] = None
    bias_adjusted_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    bias_adjusted_relative_humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None


class WeatherModelPredictionValues(BaseWeatherPredictionValues):
    """The predicted weather values with delta precipitation."""

    delta_precipitation: Optional[float] = None


class WeatherStationModelPredictionValues(BaseWeatherPredictionValues):
    """The predicted weather values for a station with 24 hour precipitation."""

    id: str
    abbreviation: str
    precip_24hours: Optional[float] = None
    station: WeatherStation
    update_date: datetime


class WeatherModelRun(BaseModel):
    """Detail about the model run"""

    datetime: datetime
    name: str
    abbreviation: str
    projection: str


class WeatherModelPrediction(BaseModel):
    """Weather model prediction for a particular weather station."""

    station: WeatherStation
    model_run: Optional[WeatherModelRun] = None
    values: List[WeatherModelPredictionValues] = []


class ModelRunPredictions(BaseModel):
    """Predictions for a model run"""

    model_run: Optional[WeatherModelRun] = None
    values: List[WeatherModelPredictionValues] = []


class WeatherStationModelRunsPredictions(BaseModel):
    """Weather model run and predictions for a station."""

    station: WeatherStation
    model_runs: List[ModelRunPredictions]


class WeatherStationsModelRunsPredictionsResponse(BaseModel):
    """Response containing a number of weather predictions for a number of weather model runs for a number
    of stations."""

    stations: List[WeatherStationModelRunsPredictions]


class ModelPredictionDetails(BaseModel):
    prediction_timestamp: datetime
    update_date: datetime
    abbreviation: str
    prediction_run_timestamp: datetime
    prediction_model_run_timestamp_id: int
    station_code: int
    rh_tgl_2: Optional[float] = None
    tmp_tgl_2: Optional[float] = None
    bias_adjusted_temperature: Optional[float] = None
    bias_adjusted_rh: Optional[float] = None
    bias_adjusted_wind_speed: Optional[float] = None
    bias_adjusted_wdir: Optional[float] = None
    precip_24h: Optional[float] = None
    bias_adjusted_precip_24h: Optional[float] = None
    wdir_tgl_10: Optional[float] = None
    wind_tgl_10: Optional[float] = None
