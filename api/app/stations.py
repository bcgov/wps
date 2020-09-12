""" Get stations (from wildfire one, or local - depending on configuration.)
"""
import os
import asyncio
import logging
from typing import List
import json
from app.schemas import WeatherStation
from app import wildfire_one

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'data/weather_stations.json')


def _get_stations_local() -> List[dict]:
    """ Get list of stations from local json files.
    """
    logger.info('Using pre-generated json to retrieve station list')
    with open(weather_stations_file_path) as weather_stations_file:
        json_data = json.load(weather_stations_file)
        return json_data['weather_stations']


def _get_stations_by_codes_local(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from local json files. """
    logger.info('Using pre-generated json to retrieve station by code')
    with open(weather_stations_file_path) as file_pointer:
        stations = json.load(file_pointer)
        results = []
        for station in stations['weather_stations']:
            if int(station['code']) in station_codes:
                results.append(WeatherStation(**station))
        return results


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    if wildfire_one.use_wfwx():
        return await wildfire_one.get_stations_by_codes(station_codes)
    return _get_stations_by_codes_local(station_codes)


async def get_stations() -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    # Check if we're really using the api, or loading from pre-generated files.
    if wildfire_one.use_wfwx():
        return await wildfire_one.get_stations()
    return _get_stations_local()


def get_stations_sync() -> List[WeatherStation]:
    """ Get list of stations - blocking call
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_stations())
