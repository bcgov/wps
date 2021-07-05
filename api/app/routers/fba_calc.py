""" Routers for Fire Behaviour Advisory Calculator """

import logging
from typing import List
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Request, Depends
import math
import app
from app.auth import authentication_required, audit
from app.schemas.fba_calc import StationsListResponse, StationResponse
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies,
                                       get_stations_by_codes)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.get('/stations', response_model=StationsListResponse)
async def get_stations_data(response: Response, request: Request,  _=Depends(authentication_required)):
    """ Returns per-station data for a list of requested stations """
    logger.info('/fba-calc/stations')

    # parse the request
    station_requests = List
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


def get_fire_type(crown_fraction_burned: int):
    """ Returns Fire Type (as str) based on percentage Crown Fraction Burned (CFB).
    These definitions come from the Red Book (p. 69).
    Abbreviations for fire types have been chosen arbitrarily.

    CROWN FRACTION BURNED           TYPE OF FIRE                ABBREV.
    < 10%                           Surface fire                SUR
    10-89%                          Intermittent crown fire     IC
    > 90%                           Continuous crown fire       CC
    """
    if crown_fraction_burned < 10:
        return 'SUR'
    elif crown_fraction_burned < 90:
        return 'IC'
    elif crown_fraction_burned >= 90:
        return 'CC'
    else:
        logger.error('Cannot calculate fire type. Invalid Crown Fraction Burned percentage received.')
        raise Exception


def get_30_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size after 30 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md).

    30 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 30 * ROS
    """
    return (math.pi * (30 * rate_of_spread) ^ 2) / (40000 * length_breadth_ratio)


def get_60_minutes_fire_size(length_breadth_ratio: float, rate_of_spread: float):
    """ Returns estimated fire size after 60 minutes, based on LB ratio and ROS.
    Formula derived from sample HFI workbook (see HFI_spreadsheet.md)

    60 min fire size = (pi * spread^2) / (40,000 * LB ratio)
    where spread = 60 * ROS
    """
    return (math.pi * (60 * rate_of_spread) ^ 2) / (40000 * length_breadth_ratio)
