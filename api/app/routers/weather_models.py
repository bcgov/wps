""" Routers for weather_models.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from app.auth import authenticate
import app.time_utils as time_utils
from app.weather_models import ModelEnum
from app.schemas.weather_models import (
    WeatherModelPredictionSummaryResponse,
    WeatherStationsModelRunsPredictionsResponse)
from app.schemas.shared import WeatherDataRequest
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
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns a summary of predictions for a given model. """
    try:
        logger.info('/weather_models/%s/predictions/summaries/', model.name)

        if request.time_of_interest is not None:
            time_of_interest = datetime.fromisoformat(request.time_of_interest)
        else:
            time_of_interest = time_utils.get_utc_now()

        summaries = await fetch_model_prediction_summaries(model, request.stations, time_of_interest)

        return WeatherModelPredictionSummaryResponse(summaries=summaries)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.post('/{model}/predictions/most_recent/',
             response_model=WeatherStationsModelRunsPredictionsResponse)
async def get_most_recent_model_values(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    """
    try:
        logger.info('/weather_models/%s/predictions/most_recent/', model.name)

        if request.time_of_interest is not None:
            time_of_interest = datetime.fromisoformat(request.time_of_interest)
        else:
            time_of_interest = time_utils.get_utc_now()

        station_predictions = await fetch_model_run_predictions_by_station_code(
            model, request.stations, time_of_interest)

        return WeatherStationsModelRunsPredictionsResponse(
            stations=station_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
