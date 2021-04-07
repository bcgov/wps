""" Get stations (from wildfire one, or local - depending on configuration.)
"""
import os
import asyncio
import logging
import enum
from typing import List
import json
from app.schemas.stations import WeatherStation
from app import wildfire_one

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'data/weather_stations.json')


class StationSourceEnum(enum.Enum):
    """ Station list sources.
    We currently have two sources for station listing, local json file, or wildfire one api.
    If the source is unspecified, configuration will govern which is used.
    """
    Unspecified = 'unspecified'  # Configuration wins.
    WildfireOne = 'wildfire_one'  # Use wildfire one as source.
    LocalStorage = 'local_storage'  # Use local storage as source.


def _get_stations_local() -> List[WeatherStation]:
    """ Get list of stations from local json files.
    """
    logger.info('Using pre-generated json to retrieve station list')
    with open(weather_stations_file_path) as weather_stations_file:
        json_data = json.load(weather_stations_file)
        results = []
        for station in json_data['weather_stations']:
            results.append(WeatherStation(**station))
        return results


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
        logger.info('Fetching stations from WFWX')
        return await wildfire_one.get_stations_by_codes(station_codes)
    return _get_stations_by_codes_local(station_codes)


async def get_stations(
        station_source: StationSourceEnum = StationSourceEnum.Unspecified) -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    if station_source == StationSourceEnum.Unspecified:
        # If station source is unspecified, check configuration:
        if wildfire_one.use_wfwx():
            return await wildfire_one.get_stations()
        return _get_stations_local()
    if station_source == StationSourceEnum.WildfireOne:
        # Get from wildfire one:
        return await wildfire_one.get_stations()
    # Get from local:
    return _get_stations_local()


def get_stations_synchronously() -> List[WeatherStation]:
    """ Get list of stations - in a synchronous/blocking call.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_stations())
