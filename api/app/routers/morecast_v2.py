""" Routes for Morecast v2 """
import logging
from fastapi import APIRouter, Response, Depends
from app.auth import (auth_with_forecaster_role_required,
                      authentication_required,
                      audit)
from app.schemas.morecast_v2 import MorecastForecast


logger = logging.getLogger(__name__)


no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/morecast-v2",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.get("/forecast")
async def get_forecast(response: Response, _=Depends(authentication_required)):
    """ Return forecasts """
    logger.info('/forecasts/')
    response.headers["Cache-Control"] = no_cache


@router.post("/forecast")
async def save_forecast(forecast: MorecastForecast, response: Response, _=Depends(auth_with_forecaster_role_required)):
    """ Persist a forecast """
    logger.info('/forecast')
    response.headers["Cache-Control"] = no_cache
    logger.info(f'Forecasting for station: {forecast.station_code}')
