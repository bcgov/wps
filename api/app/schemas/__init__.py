""" This module contains pydandict schemas for the API.
"""
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel
from app.schemas.stations import (Season, WeatherStation, WeatherStationsResponse,
                                  StationCodeList)
from app.schemas.percentiles import (YearRange, PercentileRequest, StationSummary, MeanValues,
                                     CalculatedResponse)
from app.schemas.observations import (
    WeatherReading, WeatherStationHourlyReadings, WeatherStationHourlyReadingsResponse)
from app.schemas.forecasts import (NoonForecast, NoonForecastResponse,
                                   NoonForecastValue, NoonForecastSummariesResponse, NoonForecastSummary, NoonForecastSummaryValues)
from app.schemas.weather_models import (
    WeatherModelPredictionSummaryValues, WeatherModelPredictionSummary,
    WeatherModelPredictionSummaryResponse, WeatherPredictionModel, WeatherModelPrediction,
    WeatherModelPredictionValues, WeatherModelRun, ModelRunPredictions,
    WeatherStationsModelRunsPredictionsResponse, WeatherStationModelRunsPredictions,
    WeatherModelPredictionResponse)
