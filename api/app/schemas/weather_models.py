""" This module contains pydandict schemas relating to weather models for the API.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class WeatherPredictionModel(BaseModel):
    """ The full name & acronym for a weather prediction model """
    name: str
    abbrev: str


class WeatherModelPredictionSummaryValues(BaseModel):
    """ Summary of model prediction values. """
    datetime: datetime
    tmp_tgl_2_5th: float
    tmp_tgl_2_90th: float
    tmp_tgl_2_median: float
    rh_tgl_2_5th: float
    rh_tgl_2_90th: float
    rh_tgl_2_median: float


class WeatherModelPredictionSummary(BaseModel):
    """ Summary of weather predictions for a given model.
    Detail: For the global model, we end up with 20 different predictions for every three hours of any given
    day, this represents a summary of that data. """
    station: WeatherStation
    model: WeatherPredictionModel
    values: List[WeatherModelPredictionSummaryValues] = []


class WeatherModelPredictionSummaryResponse(BaseModel):
    """ Response containing prediction summaries for a given weather model."""
    summaries: List[WeatherModelPredictionSummary]


class WeatherModelPredictionValues(BaseModel):
    """ The predicted weather values. """
    datetime: datetime
    temperature: float = None
    bias_adjusted_temperature: float = None
    dew_point: float = None
    relative_humidity: float = None
    bias_adjusted_relative_humidity: float = None
    wind_speed: float = None
    wind_direction: float = None
    total_precipitation: float = None
    accumulated_rain: float = None
    accumulated_snow: float = None
    accumulated_freezing_rain: float = None
    accumulated_ice_pellets: float = None
    cloud_cover: float = None
    sea_level_pressure: float = None
    wind_speed_40m: float = None
    wind_direction_40m: float = None
    wind_direction_80m: float = None
    wind_speed_120m: float = None
    wind_direction_120m: float = None
    wind_speed_925mb: float = None
    wind_direction_925mb: float = None
    wind_speed_850mb: float = None
    wind_direction_850mb: float = None


class WeatherModelRun(BaseModel):
    """ Detail about the model run """
    datetime: datetime
    name: str
    abbreviation: str
    projection: str


class WeatherModelPrediction(BaseModel):
    """ Weather model prediction for a particular weather station. """
    station: WeatherStation
    model_run: WeatherModelRun = None
    values: List[WeatherModelPredictionValues] = []


class WeatherModelPredictionResponse(BaseModel):
    """ Response containg a number of weather predictions. """
    predictions: List[WeatherModelPrediction]


class ModelRunPredictions(BaseModel):
    """ Predictions for a model run """
    model_run: WeatherModelRun = None
    values: List[WeatherModelPredictionValues] = []


class WeatherStationModelRunsPredictions(BaseModel):
    """ Weather model run and predictions for a station. """
    station: WeatherStation
    model_runs: List[ModelRunPredictions]


class WeatherStationsModelRunsPredictionsResponse(BaseModel):
    """ Response containing a number of weather predictions for a number of weather model runs for a number
    of stations."""
    stations: List[WeatherStationModelRunsPredictions]
