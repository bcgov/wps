""" Routers for Fire Behaviour Advisory Calculator """

import logging
from typing import List
from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends
from app.auth import authentication_required, audit
from app.schemas.fba_calc import StationListRequest, StationsListResponse
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies,
                                       get_wfwx_stations_from_station_codes)


router = APIRouter(
    prefix="/fba-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)

logger = logging.getLogger(__name__)


@router.post('/stations', response_model=StationsListResponse)
async def get_stations_data(
        request: StationListRequest,
        _=Depends(authentication_required)
):
    """ Returns per-station data for a list of requested stations """
    logger.info('/fba-calc/stations')

    try:

        # parse the request
        station_codes = [station.station_code for station in request.stations]

        async with ClientSession() as session:
            header = await get_auth_header(session)
            wfwx_stations = await get_wfwx_stations_from_station_codes(
                session, header, station_codes)
            dailies = await get_dailies(
                session, header, wfwx_stations, request.stations)
            return StationsListResponse(stations=dailies)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
