""" Routers for weather_models.
"""
import logging
import datetime
from fastapi import APIRouter, Depends
from app.auth import authenticate
import app.time_utils as time_utils
from app.weather_models import ModelEnum, ProjectionEnum
from app.schemas.weather_models import (
    WeatherModelPredictionResponse,
    WeatherModelPredictionSummaryResponse,
    WeatherStationsModelRunsPredictionsResponse)
from app.schemas.stations import StationCodeList
from app.weather_models.fetch.summaries import fetch_model_prediction_summaries
from app.weather_models.fetch.predictions import (
    fetch_model_run_predictions_by_station_code)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather_models",
    dependencies=[Depends(authenticate)],
)


@router.post('/{model}/predictions/summaries/',
             response_model=WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: StationCodeList):
    """ Returns a summary of predictions for a given model. """
    try:
        logger.info('/weather_models/%s/predictions/summaries/', model.name)
        summaries = await fetch_model_prediction_summaries(model, request.stations)
        return WeatherModelPredictionSummaryResponse(summaries=summaries)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.post('/{model}/predictions/most_recent/',
             response_model=WeatherStationsModelRunsPredictionsResponse)
async def get_most_recent_model_values(
        model: ModelEnum, request: StationCodeList):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    """
    try:
        logger.info('/weather_models/%s/predictions/most_recent/', model.name)
        end_date = time_utils.get_utc_now() + datetime.timedelta(days=10)
        station_predictions = await fetch_model_run_predictions_by_station_code(
            model, request.stations, end_date)
        return WeatherStationsModelRunsPredictionsResponse(
            stations=station_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
