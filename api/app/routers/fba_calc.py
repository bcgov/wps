""" Routers for Fire Behaviour Advisory Calculator """

import logging
from typing import List
from aiohttp.client import ClientSession
from fastapi import APIRouter, Request, Depends
from app.auth import authentication_required, audit
from app.schemas.fba_calc import StationsListResponse
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
        request: Request,
        _=Depends(authentication_required)):
    """ Returns per-station data for a list of requested stations """
    logger.info('/fba-calc/stations')

    # parse the request
    station_requests = List
    station_codes = List[int]
    for station in request.json:
        station_request = {
            'station_code': station['station_code'],
            'date': station['date'],
            'fuel_type': station['fuel_type'],
            'percentage_conifer': station['percentage_conifer'],
            'grass_cure': station['grass_cure'],
            'crown_burn_height': station['crown_burn_height']
        }
        station_requests.append(station_request)
        station_codes.append(station['station_code'])

    async with ClientSession() as session:
        header = await get_auth_header(session)
        wfwx_stations = await get_wfwx_stations_from_station_codes(
            session, header, station_codes)
        dailies = await get_dailies(
            session, header, wfwx_stations, station_requests)
        return StationsListResponse(stations=dailies)
