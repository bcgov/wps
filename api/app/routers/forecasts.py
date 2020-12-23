""" Routers for forecasts.
"""
import logging
import datetime
from fastapi import APIRouter, Depends
from app.auth import authenticate
from app.schemas.forecasts import NoonForecastResponse, NoonForecastSummariesResponse
from app.schemas.stations import StationCodeList
from app.forecasts.noon_forecasts import fetch_noon_forecasts
from app.forecasts.noon_forecasts_summaries import fetch_noon_forecasts_summaries
import app.time_utils as time_utils


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/forecasts",
    dependencies=[Depends(authenticate)],
)


@router.post('/noon/', response_model=NoonForecastResponse)
def get_noon_forecasts(request: StationCodeList):
    """ Returns noon forecasts pulled from BC FireWeather Phase 1 website for the specified
    set of weather stations. """
    try:
        logger.info('/noon/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        forward_5_days = now + datetime.timedelta(days=5)
        return fetch_noon_forecasts(request.stations, back_5_days, forward_5_days)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.post('/noon/summaries/', response_model=NoonForecastSummariesResponse)
async def get_noon_forecasts_summaries(request: StationCodeList):
    """ Returns summaries of noon forecasts for given weather stations """
    try:
        logger.info('/noon/summaries/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        return await fetch_noon_forecasts_summaries(request.stations, back_5_days, now)

    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
