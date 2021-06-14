""" Routers for HFI Calculator """
import logging
import math
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from app.wildfire_one import (get_ids_from_station_codes,
                              get_dailies,
                              get_auth_header)
from app.auth import authentication_required
from app.utils.time import get_utc_today_start_and_end
from app.schemas.hfi_calc import StationDailyResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
)


def validate_time_range(start_time_stamp: Optional[int], end_time_stamp: Optional[int]):
    """ Sets timestamp to today if they are None.
        Defaults to start of today and end of today if no range is given. """
    if start_time_stamp is None or end_time_stamp is None:
        today_start, today_end = get_utc_today_start_and_end()
        return math.floor(today_start.timestamp()*1000), math.floor(today_end.timestamp()*1000)
    return int(start_time_stamp), int(end_time_stamp)


@router.get('/daily', response_model=StationDailyResponse)
async def get_daily_view(response: Response,
                         station_codes: Optional[List[int]] = Query(None),
                         start_time_stamp: Optional[int] = None,
                         end_time_stamp: Optional[int] = None):
    """ Returns daily metrics for each station code. """
    try:
        logger.info('/hfi-calc/daily')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        valid_start_time, valid_end_time = validate_time_range(start_time_stamp, end_time_stamp)

        async with ClientSession() as session:
            header = await get_auth_header(session)
            valid_station_codes = await get_ids_from_station_codes(session, header, station_codes)
            dailies = await get_dailies(
                session, header, valid_station_codes, valid_start_time, valid_end_time)
            return StationDailyResponse(dailies=dailies)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
