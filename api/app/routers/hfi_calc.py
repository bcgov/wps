""" Routers for HFI Calculator """
import logging
from datetime import datetime
from typing import List
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends
from app import wildfire_one
from app.auth import authentication_required
from app.schemas.hfi_calc import StationDailyResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
)


@router.get('/daily', response_model=StationDailyResponse)
async def get_daily_view(response: Response,
                         start_time_stamp: datetime,
                         end_time_stamp: datetime,
                         station_codes: List[int],
                         _=Depends(authentication_required)):
    """ Returns daily metrics for each station code. """
    try:
        logger.info('/hfi-calc/daily')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this

        async with ClientSession() as session:
            header = await wildfire_one.get_auth_header(session)
            return await wildfire_one.get_dailies(
                session, header, station_codes, start_time_stamp, end_time_stamp)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
