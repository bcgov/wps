""" Routers for weather_models.
"""
import logging
from fastapi import APIRouter, Depends
from datetime import date, datetime, time
from app.auth import authentication_required, audit
from app.weather_models import ModelEnum
from app.schemas.weather_models import (
    WeatherModelPredictionSummaryResponse,
    WeatherStationsModelRunsPredictionsResponse)
from app.schemas.shared import ModelDataRequest, WeatherDataRequest
from app.weather_models.fetch.summaries import fetch_model_prediction_summaries
from app.weather_models.fetch.predictions import (
    fetch_model_run_predictions_by_station_code,
    fetch_model_run_predictions_by_station_code_and_date_range)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather_models",
    dependencies=[Depends(audit), Depends(authentication_required)],
)


@router.post('/{model}/predictions/summaries/',
             response_model=WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns a summary of predictions for a given model. """
    logger.info('/weather_models/%s/predictions/summaries/', model.name)

    summaries = await fetch_model_prediction_summaries(model, request.stations, request.time_of_interest)

    return WeatherModelPredictionSummaryResponse(summaries=summaries)


@router.post('/{model}/predictions/most_recent/',
             response_model=WeatherStationsModelRunsPredictionsResponse)
async def get_most_recent_model_values(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    """
    logger.info('/weather_models/%s/predictions/most_recent/', model.name)

    station_predictions = await fetch_model_run_predictions_by_station_code(
        model, request.stations, request.time_of_interest)

    return WeatherStationsModelRunsPredictionsResponse(
        stations=station_predictions)


@router.post('/{model}/predictions/most_recent/{start_date}/{end_date}',
             response_model=WeatherStationsModelRunsPredictionsResponse)
async def get_model_values_for_date_range(
        model: ModelEnum, start_date: date, end_date: date, request: ModelDataRequest):
    """ Returns the weather values for the last model prediction for the 
    requested stations within the requested date range.
    """
    logger.info('/weather_models/%s/predictions/most_recent/%s/%s', model.name, start_date, end_date)

    start_time = datetime.combine(start_date, time.min)
    end_time = datetime.combine(end_date, time.max)

    station_predictions = await fetch_model_run_predictions_by_station_code_and_date_range(
        model, request.stations, start_time, end_time)

    return WeatherStationsModelRunsPredictionsResponse(
        stations=station_predictions)
