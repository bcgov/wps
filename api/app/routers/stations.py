""" Routers for stations """
import logging
from datetime import datetime
from fastapi import APIRouter, Response, Depends
from wps_shared.auth import authentication_required, audit
from wps_shared.utils.time import get_utc_now, get_hour_20
from wps_shared.schemas.stations import (
    WeatherStationGroupsMemberRequest,
    WeatherStationsResponse,
    DetailedWeatherStationsResponse,
    WeatherStationGroupsResponse,
    WeatherStationGroupMembersResponse,
)
from wps_shared.stations import get_stations_as_geojson, fetch_detailed_stations_as_geojson
from wps_shared.wildfire_one import wfwx_api


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stations",
)

no_cache = "max-age=0"  # don't let the browser cache this


@router.get('/details/', response_model=DetailedWeatherStationsResponse)
async def get_detailed_stations(response: Response, toi: datetime = None, __=Depends(audit), _=Depends(authentication_required)):
    """ Returns a list of fire weather stations with detailed information.
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/details/')
        response.headers["Cache-Control"] = no_cache
        if toi is None:
            # NOTE: Don't be tempted to move this into the function definition. It's not possible
            # to mock a function if it's part of the function definition, and will cause
            # tests to fail.
            toi = get_utc_now()
        else:
            toi = get_hour_20(toi)
        weather_stations = await fetch_detailed_stations_as_geojson(toi)
        return DetailedWeatherStationsResponse(features=weather_stations)

    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/', response_model=WeatherStationsResponse)
async def get_stations(response: Response):
    """ Return a list of fire weather stations.
    Stations source can be:
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/')

        weather_stations = await get_stations_as_geojson()
        response.headers["Cache-Control"] = no_cache

        return WeatherStationsResponse(features=weather_stations)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/groups', response_model=WeatherStationGroupsResponse)
async def get_station_groups(response: Response, _=Depends(authentication_required)):
    """ Return a list of all station groups available in from WildFireOne
        Groups are retrieved from an undocumented stationGroups endpoint.
    """
    logger.info('/stations/groups')
    groups = await wfwx_api.get_station_groups()
    response.headers["Cache-Control"] = no_cache
    return WeatherStationGroupsResponse(groups=groups)


@router.post('/groups/members', response_model=WeatherStationGroupMembersResponse)
async def get_stations_by_group_ids(groups_request: WeatherStationGroupsMemberRequest, response: Response, _=Depends(authentication_required)):
    """ Return a list of stations that are part of the specified group(s) """
    logger.info('/stations/groups/members')
    stations = await wfwx_api.get_stations_by_group_ids([id for id in groups_request.group_ids])
    response.headers["Cache-Control"] = no_cache
    return WeatherStationGroupMembersResponse(stations=stations)
