""" Get stations (from wildfire one, or local - depending on configuration.)
"""
import os
from datetime import datetime
import math
import asyncio
import logging
from typing import List, Final
import json
from aiohttp import TCPConnector
from aiohttp.client import ClientSession
from sqlalchemy.engine.row import Row
from wps_wf1.wfwx_api import WfwxApi
import wps_shared.db.database
from wps_shared.schemas.stations import (
    WeatherStation,
    GeoJsonWeatherStation,
    GeoJsonDetailedWeatherStation,
    WeatherStationProperties,
    WeatherVariables,
    DetailedWeatherStationProperties,
    WeatherStationGeometry,
)
from wps_shared.db.crud.stations import get_noon_forecast_observation_union

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'data/weather_stations.json')


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """Get a list of stations by code, from WFWX Fireweather API."""
    # Limit the number of concurrent connections.
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as session:
        wfwx_api = WfwxApi(session)
        return await wfwx_api.get_stations_by_codes(station_codes)


async def get_stations_as_geojson() -> List[GeoJsonWeatherStation]:
    """ Format stations to conform to GeoJson spec """
    geojson_stations = []
    stations = await get_stations_asynchronously()
    for station in stations:
        geojson_stations.append(
            GeoJsonWeatherStation(properties=WeatherStationProperties(
                code=station.code,
                name=station.name,
                ecodivision_name=station.ecodivision_name,
                core_season=station.core_season),
                geometry=WeatherStationGeometry(coordinates=[station.long, station.lat])))
    return geojson_stations


async def get_stations_asynchronously():
    """ Get list of stations asynchronously """
    async with ClientSession() as session:
        wfwx_api = WfwxApi(session)
        return await wfwx_api.get_station_data()


def get_stations_synchronously() -> List[WeatherStation]:
    """ Get list of stations - in a synchronous/blocking call.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_stations_asynchronously())