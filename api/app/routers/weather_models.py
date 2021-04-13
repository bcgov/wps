""" Routers for weather_models.
"""
import logging
from fastapi import APIRouter, Depends
from app.dependency import authentication_required, audit
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
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.post('/{model}/predictions/summaries/',
             response_model=WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns a summary of predictions for a given model. """
    try:
        logger.info('/weather_models/%s/predictions/summaries/', model.name)

        summaries = await fetch_model_prediction_summaries(model, request.stations, request.time_of_interest)

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

        station_predictions = await fetch_model_run_predictions_by_station_code(
            model, request.stations, request.time_of_interest)

        return WeatherStationsModelRunsPredictionsResponse(
            stations=station_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
