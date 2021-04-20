""" Get stations (from wildfire one, or local - depending on configuration.)
"""
import os
from datetime import datetime
import math
import asyncio
import logging
import enum
from typing import List, Final
import json
from app import wildfire_one
from app.schemas.stations import (WeatherStation,
                                  GeoJsonWeatherStation,
                                  GeoJsonDetailedWeatherStation,
                                  WeatherStationProperties,
                                  WeatherVariables,
                                  DetailedWeatherStationProperties,
                                  WeatherStationGeometry)
from app.db.database import get_read_session_scope
from app.db.crud.stations import get_noon_forecast_observation_union

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


def _set_weather_variables(station_properties: DetailedWeatherStationProperties, station_union: object):
    """
    Helper function to set the observed and forecast values on the detailed weather station properties.
    """
    variable_names: Final = ('temperature', 'relative_humidity')
    # Iterate through variables (temp, r.h. etc. etc.)
    for variable_name in variable_names:
        # Get the variable (e.g. temp)
        value = station_union[variable_name]
        if not math.isnan(value):
            # Is this a forecast or an observation?
            record_type = station_union['record_type']
            weather_variables = getattr(station_properties, record_type, None)
            if weather_variables is None:
                # Make on if we don't have one yet.
                weather_variables = WeatherVariables()
                # Set it on the station_properties.
                setattr(station_properties, record_type, weather_variables)
            # Set the value (e.g. temp) on the weather variables (e.g. on observed)
            setattr(weather_variables, variable_name, value)


def _get_detailed_stations(time_of_interest: datetime):
    """ Get a list of weather stations with details using a combination of static json and database
    records. """
    geojson_stations = []
    # this gets us a list of stations
    stations = _get_stations_local()
    with get_read_session_scope() as session:
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
            station = station_lookup.get(station_union['station_code'], None)
            if station:
                _set_weather_variables(station.properties, station_union)
    return geojson_stations


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
    """ Get list of stations from some source (ideally WFWX Fireweather API)
    """
    if station_source == StationSourceEnum.Unspecified:
        # If station source is unspecified, check configuration:
        if wildfire_one.use_wfwx():
            return await wildfire_one.get_stations()
    elif station_source == StationSourceEnum.WildfireOne:
        # Get from wildfire one:
        return await wildfire_one.get_stations()
    # Get from local:
    return _get_stations_local()


async def fetch_detailed_stations_as_geojson(
        time_of_interest: datetime,
        station_source: StationSourceEnum) \
        -> List[GeoJsonDetailedWeatherStation]:
    """ Fetch a detailed list of stations. i.e. more than just the fire station name and code,
    throw some observations and forecast in the mix. """
    if station_source == StationSourceEnum.WildfireOne or (
            station_source == StationSourceEnum.Unspecified and wildfire_one.use_wfwx()):
        # Get from wildfire one:
        logger.info('requesting detailed stations...')
        result = await wildfire_one.get_detailed_stations(time_of_interest)
        logger.info('detailed stations loaded.')
        return result
    # Get from local:
    return _get_detailed_stations(time_of_interest)


async def get_stations_as_geojson(
        station_source: StationSourceEnum = StationSourceEnum.Unspecified) -> List[GeoJsonWeatherStation]:
    """ Format stations to conform to GeoJson spec """
    geojson_stations = []
    stations = await get_stations(station_source)
    for station in stations:
        geojson_stations.append(
            GeoJsonWeatherStation(properties=WeatherStationProperties(
                code=station.code,
                name=station.name,
                ecodivision_name=station.ecodivision_name,
                core_season=station.core_season),
                geometry=WeatherStationGeometry(coordinates=[station.long, station.lat])))
    return geojson_stations


def get_stations_synchronously() -> List[WeatherStation]:
    """ Get list of stations - in a synchronous/blocking call.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_stations())
