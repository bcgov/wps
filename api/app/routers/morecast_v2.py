""" Routes for Morecast v2 """
import logging
from typing import List
from fastapi import APIRouter, Response, Depends, status
from datetime import date
from app.auth import (auth_with_forecaster_role_required,
                      authentication_required,
                      audit)
from app.db.crud.morecast_v2 import get_user_forecasts_for_date, save_all_forecasts
from app.db.database import get_read_session_scope, get_write_session_scope
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.schemas.morecast_v2 import MorecastForecastRequest, MorecastForecastResponse
from app.utils.time import get_datetime_from_utc_timestamp, get_utc_now


logger = logging.getLogger(__name__)


no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/morecast-v2",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.get("/forecasts/{for_date}")
async def get_forecast(for_date: date,
                       response: Response,
                       token=Depends(authentication_required)) -> List[MorecastForecastResponse]:
    """ Return forecasts """
    logger.info('/forecasts/')
    response.headers["Cache-Control"] = no_cache

    username = token.get('idir_username', None)

    with get_read_session_scope() as db_session:
        return get_user_forecasts_for_date(db_session, username, for_date)


@router.post("/forecast", status_code=status.HTTP_201_CREATED)
async def save_forecast(forecasts: List[MorecastForecastRequest],
                        response: Response,
                        token=Depends(auth_with_forecaster_role_required)) -> List[MorecastForecastResponse]:
    """ Persist a forecast """
    logger.info('/forecast')
    response.headers["Cache-Control"] = no_cache
    logger.info('Saving %s forecasts', len(forecasts))

    username = token.get('idir_username', None)
    now = get_utc_now()

    forecasts_to_save = [MorecastForecastRecord(station_code=forecast.station_code,
                                                for_date=get_datetime_from_utc_timestamp(forecast.for_date),
                                                temp=forecast.temp,
                                                rh=forecast.rh,
                                                precip=forecast.precip,
                                                wind_speed=forecast.wind_speed,
                                                wind_direction=forecast.wind_direction,
                                                create_user=username,
                                                create_timestamp=now,
                                                update_user=username,
                                                update_timestamp=now) for forecast in forecasts]
    with get_write_session_scope() as db_session:
        save_all_forecasts(db_session, forecasts_to_save)
        return [MorecastForecastResponse(station_code=forecast.station_code,
                                         for_date=forecast.for_date,
                                         temp=forecast.temp,
                                         rh=forecast.rh,
                                         precip=forecast.precip,
                                         wind_speed=forecast.wind_speed,
                                         wind_direction=forecast.wind_direction,
                                         update_timestamp=int(now.timestamp() * 1000)) for forecast in forecasts]
