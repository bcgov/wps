""" Routes for Morecast v2 """
import logging
from typing import List
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


@router.get("/forecasts")
async def get_forecast(response: Response, _=Depends(authentication_required)):
    """ Return forecasts """
    logger.info('/forecasts/')
    response.headers["Cache-Control"] = no_cache


@router.post("/forecast")
async def save_forecast(forecasts: List[MorecastForecast],
                        response: Response,
                        _=Depends(auth_with_forecaster_role_required)):
    """ Persist a forecast """
    logger.info('/forecast')
    response.headers["Cache-Control"] = no_cache
    logger.info('Saving %s forecasts', len(forecasts))
