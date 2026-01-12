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
    DetailedWeatherStationProperties,
    GeoJsonDetailedWeatherStation,
    GeoJsonWeatherStation,
    WeatherStation,
    WeatherStationGeometry,
    WeatherStationProperties,
    WeatherVariables,
)
from wps_shared.db.crud.stations import _get_noon_date, get_noon_forecast_observation_union

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'data/weather_stations.json')


def _get_stations_local() -> List[WeatherStation]:
    """ Get list of stations from local json files.
    """
    logger.info('Using pre-generated json to retrieve station list')
    with open(weather_stations_file_path, encoding="utf-8") as weather_stations_file:
        json_data = json.load(weather_stations_file)
        results = []
        for station in json_data['weather_stations']:
            results.append(WeatherStation(**station))
        return results


def _set_weather_variables(station_properties: DetailedWeatherStationProperties, station_union: Row):
    """
    Helper function to set the observed and forecast values on the detailed weather station properties.
    """
    variable_names: Final = ('temperature', 'relative_humidity')
    # Iterate through variables (temp, r.h. etc. etc.)
    for variable_name in variable_names:
        # Get the variable (e.g. temp)
        value = getattr(station_union, variable_name)
        if not math.isnan(value):
            # Is this a forecast or an observation?
            record_type = getattr(station_union, 'record_type')
            weather_variables = getattr(station_properties, record_type, None)
            if weather_variables is None:
                # Make on if we don't have one yet.
                weather_variables = WeatherVariables()
                # Set it on the station_properties.
                setattr(station_properties, record_type, weather_variables)
            # Set the value (e.g. temp) on the weather variables (e.g. on observed)
            setattr(weather_variables, variable_name, value)


async def _get_detailed_stations(time_of_interest: datetime):
    """ Get a list of weather stations with details using a combination of static json and database
    records. """
    geojson_stations = []
    # this gets us a list of stations
    stations = await get_stations_asynchronously()
    with wps_shared.db.database.get_read_session_scope() as session:
        stations_detailed = get_noon_forecast_observation_union(session, time_of_interest)
        station_lookup = {}
        for station in stations:
            geojson_station = GeoJsonDetailedWeatherStation(properties=DetailedWeatherStationProperties(
                code=station.code,
                name=station.name,
                ecodivision_name=station.ecodivision_name,
                core_season=station.core_season),
                geometry=WeatherStationGeometry(coordinates=[station.long, station.lat]))
            station_lookup[station.code] = geojson_station
            geojson_stations.append(geojson_station)
        for station_union in stations_detailed:
            station = station_lookup.get(getattr(station_union, 'station_code'), None)
            if station:
                _set_weather_variables(station.properties, station_union)
    return geojson_stations


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """Get a list of stations by code, from WFWX Fireweather API."""
    # Limit the number of concurrent connections.
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as session:
        wfwx_api = WfwxApi(session)
        return await wfwx_api.get_stations_by_codes(station_codes)


async def get_stations_from_source() -> List[WeatherStation]:
    """Get list of stations from some source (ideally WFWX Fireweather API)"""
    return await get_stations_asynchronously()


async def fetch_detailed_stations_as_geojson(time_of_interest: datetime) -> List[GeoJsonDetailedWeatherStation]:
    """Fetch a detailed list of stations. i.e. more than just the fire station name and code,
    throw some observations and forecast in the mix."""
    logger.info("requesting detailed stations...")
    noon_time_of_interest = _get_noon_date(time_of_interest)
    async with ClientSession() as session:
        wfwx_api = WfwxApi(session)
        result = await wfwx_api.get_detailed_stations(noon_time_of_interest)
    logger.info("detailed stations loaded.")
    return result


async def get_stations_as_geojson() -> List[GeoJsonWeatherStation]:
    """ Format stations to conform to GeoJson spec """
    geojson_stations = []
    stations = await get_stations_from_source()
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
    return loop.run_until_complete(get_stations_from_source())
