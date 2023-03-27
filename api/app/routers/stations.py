""" Routers for stations """
import logging
from datetime import datetime
from fastapi import APIRouter, Response, Depends
from app.auth import authentication_required, audit
from app.utils.time import get_utc_now, get_hour_20
from app.schemas.stations import (WeatherStationsResponse, DetailedWeatherStationsResponse, WeatherStationGroupsResponse,
                                  WeatherStationGroupMembersResponse)
from app.stations import StationSourceEnum, get_stations_as_geojson, fetch_detailed_stations_as_geojson
from app.wildfire_one import wfwx_api


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stations",
)


@router.get('/details/', response_model=DetailedWeatherStationsResponse)
async def get_detailed_stations(response: Response,
                                toi: datetime = None,
                                source: StationSourceEnum = StationSourceEnum.WILDFIRE_ONE,
                                __=Depends(audit),
                                _=Depends(authentication_required)):
    """ Returns a list of fire weather stations with detailed information.
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/details/')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        if toi is None:
            # NOTE: Don't be tempted to move this into the function definition. It's not possible
            # to mock a function if it's part of the function definition, and will cause
            # tests to fail.
            toi = get_utc_now()
        else:
            toi = get_hour_20(toi)
        weather_stations = await fetch_detailed_stations_as_geojson(toi, source)
        return DetailedWeatherStationsResponse(features=weather_stations)

    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/', response_model=WeatherStationsResponse)
async def get_stations(response: Response,
                       source: StationSourceEnum = StationSourceEnum.UNSPECIFIED):
    """ Return a list of fire weather stations.
    Stations source can be:
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/')

        weather_stations = await get_stations_as_geojson(source)
        response.headers["Cache-Control"] = "max-age=0"  # let browsers to cache the data for 12 hours

        return WeatherStationsResponse(features=weather_stations)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/groups', response_model=WeatherStationGroupsResponse)
async def get_station_groups(response: Response):
    """ Return a list of all station groups available in from WildFireOne
        Groups are retrieved from an undocumented stationGroups endpoint.
    """
    try:
        logger.info('/stations/groups')
        groups = await wfwx_api.get_station_groups()
        response.headers["Cache-Control"] = "max-age=0"
        return WeatherStationGroupsResponse(groups_by_owner=groups)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/groups/{group_id}/members', response_model=WeatherStationGroupMembersResponse)
async def get_stations_by_group_id(group_id: str, response: Response):
    """ Return a list of stations that are part of teh specified group """
    try:
        logger.info('/stations/groups/.../members}')
        stations = await wfwx_api.get_stations_by_group_id(group_id)
        response.headers["Cache-Control"] = "max-age=0"
        return WeatherStationGroupMembersResponse(stations=stations)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
