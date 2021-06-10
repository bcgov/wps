""" Routers for HFI Calculator """
from os import stat
from api.app.utils.time import get_utc_now
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends
from app import wildfire_one
from app.auth import authentication_required
from app.schemas.hfi_calc import StationDailyResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
)


def validate_time_range(start_time_stamp: Optional[int], end_time_stamp: Optional[int]):
    """ Sets timestamp to today if they are None. """
    if start_time_stamp is None or end_time_stamp is None:
        return get_utc_now(), get_utc_now() + timedelta(days=1)
    else:
        return int(start_time_stamp), int(end_time_stamp)


def validate_station_codes(station_codes: Optional[List[int]]):
    """ Validates empty or missing station lists """
    if station_codes is None:
        return []
    else:
        return [station_code for station_code in station_codes]


@router.get('/daily', response_model=StationDailyResponse)
async def get_daily_view(response: Response,
                         station_codes: Optional[List[int]],
                         start_time_stamp: Optional[int] = None,
                         end_time_stamp: Optional[int] = None,
                         _=Depends(authentication_required)):
    """ Returns daily metrics for each station code. """
    try:
        logger.info('/hfi-calc/daily')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        valid_start_time, valid_end_time = validate_time_range(start_time_stamp, end_time_stamp)
        valid_station_codes = validate_station_codes(station_codes)

        async with ClientSession() as session:
            header = await wildfire_one.get_auth_header(session)
            return await wildfire_one.get_dailies(
                session, header, valid_station_codes, valid_start_time, valid_end_time)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
