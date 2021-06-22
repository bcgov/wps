""" This module contains methods for retrieving information from the WFWX Fireweather API.
"""
import math
from typing import Generator, List, Optional
from datetime import datetime
import logging
import asyncio
from aiohttp import ClientSession, TCPConnector
from app import config
from app.utils.hfi_calculator import get_fire_centre_station_codes
from app.db.models.observations import HourlyActual
from app.schemas.hfi_calc import StationDaily
from app.schemas.observations import WeatherStationHourlyReadings
from app.schemas.stations import (WeatherStation,
                                  WeatherVariables)
from app.wildfire_one.schema_parsers import parse_station, parse_daily, parse_hourly, parse_hourly_actual
from app.wildfire_one.query_builders import (BuildQueryAllActiveStations,
                                             BuildQueryAllHourliesByRange,
                                             BuildQueryByStationCode,
                                             BuildQueryDailesByStationCode)
from app.wildfire_one.util import is_station_valid
from app.wildfire_one.wildfire_fetchers import (fetch_access_token,
                                                fetch_detailed_geojson_stations,
                                                fetch_paged_response_generator,
                                                fetch_hourlies,
                                                fetch_raw_dailies_for_all_stations)


logger = logging.getLogger(__name__)


def use_wfwx():
    """ Return True if configured to use WFWX """
    using_wfwx = config.get('USE_WFWX') == 'True'
    logger.info('USE_WFWX = %s', using_wfwx)
    return using_wfwx


async def get_auth_header(session: ClientSession) -> dict:
    """Get WFWX auth header"""
    # Fetch access token
    token = await fetch_access_token(session)
    # Construct the header.
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    return header


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    logger.info('Using WFWX to retrieve stations by code')
    async with ClientSession() as session:
        header = await get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        iterator = fetch_paged_response_generator(
            session, header, BuildQueryByStationCode(station_codes), 'stations')
        async for raw_station in iterator:
            # If the station is valid, add it to our list of stations.
            if is_station_valid(raw_station):
                stations.append(parse_station(raw_station))
        logger.debug('total stations: %d', len(stations))
        return stations


async def station_list_mapper(raw_stations: Generator[dict, None, None]):
    """ Maps raw stations to WeatherStation list"""
    stations = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if is_station_valid(raw_station):
            stations.append(WeatherStation(code=raw_station['stationCode'],
                                           name=raw_station['displayLabel'],
                                           lat=raw_station['latitude'],
                                           long=raw_station['longitude']))
    return stations


class WFWXWeatherStation():
    """ A WFWX station includes a code and WFWX API specific id """

    def __init__(self, wfwx_id: str, code: int):
        self.wfwx_id = wfwx_id
        self.code = code


async def wfwx_station_list_mapper(raw_stations: Generator[dict, None, None]) -> List[WFWXWeatherStation]:
    """ Maps raw stations to WFWXWeatherStation list"""
    stations = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if is_station_valid(raw_station):
            stations.append(WFWXWeatherStation(wfwx_id=raw_station['id'],
                                               code=raw_station['stationCode']))
    return stations


async def get_stations(session: ClientSession,
                       header: dict,
                       mapper=station_list_mapper):
    """ Get list of stations from WFWX Fireweather API.
    """
    logger.info('Using WFWX to retrieve station list')
    # Iterate through "raw" station data.
    raw_stations = fetch_paged_response_generator(
        session, header, BuildQueryAllActiveStations(), 'stations')
    # Map list of stations into desired shape
    stations = await mapper(raw_stations)
    logger.debug('total stations: %d', len(stations))
    return stations


async def get_detailed_stations(time_of_interest: datetime):
    """
    We do two things in parallel.
    # 1) list of stations
    # 2) list of noon values
    Once we've collected them all, we merge them into one response
    """
    # Limit the number of concurrent connections.
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as session:
        # Get the authentication header
        header = await get_auth_header(session)
        # Fetch the daily (noon) values for all the stations
        dailies_task = asyncio.create_task(
            fetch_raw_dailies_for_all_stations(session, header, time_of_interest))
        # Fetch all the stations
        stations_task = asyncio.create_task(fetch_detailed_geojson_stations(
            session, header, BuildQueryAllActiveStations()))

        # Await completion of concurrent tasks.
        dailies = await dailies_task
        stations, id_to_code_map = await stations_task

        # Combine dailies and stations
        for daily in dailies:
            station_id = daily.get('stationId')
            station_code = id_to_code_map.get(station_id, None)
            if station_code:
                station = stations[station_code]
                weather_variable = WeatherVariables(
                    temperature=daily.get('temperature'),
                    relative_humidity=daily.get('relativeHumidity'))
                record_type = daily.get('recordType').get('id')
                if record_type == 'ACTUAL':
                    station.properties.observations = weather_variable
                elif record_type == 'FORECAST':
                    station.properties.forecasts = weather_variable
                else:
                    logger.info('unexpected record type: %s', record_type)
            else:
                logger.debug('No station found for daily reading (%s)', station_id)

        return list(stations.values())


async def get_hourly_readings(
        session: ClientSession,
        header: dict,
        station_codes: List[int],
        start_timestamp: datetime,
        end_timestamp: datetime) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    """
    # Create a list containing all the tasks to run in parallel.
    tasks = []

    # Iterate through "raw" station data.
    iterator = fetch_paged_response_generator(
        session, header, BuildQueryByStationCode(station_codes), 'stations')
    async for raw_station in iterator:
        task = asyncio.create_task(
            fetch_hourlies(session,
                           raw_station,
                           header,
                           start_timestamp,
                           end_timestamp))
        tasks.append(task)

    # Run the tasks concurrently, waiting for them all to complete.
    return await asyncio.gather(*tasks)


async def get_hourly_actuals_all_stations(
        session: ClientSession,
        header: dict,
        start_timestamp: datetime,
        end_timestamp: datetime) -> List[HourlyActual]:
    """ Get the hourly actuals for all stations.
    """

    hourly_actuals: List[HourlyActual] = []

    # Iterate through "raw" station data.
    hourlies_iterator = fetch_paged_response_generator(
        session, header, BuildQueryAllHourliesByRange(
            math.floor(start_timestamp.timestamp()*1000),
            math.floor(end_timestamp.timestamp()*1000)), 'hourlies')

    hourlies = []
    async for hourly in hourlies_iterator:
        hourlies.append(hourly)

    stations: List[WFWXWeatherStation] = await get_stations(session, header, mapper=wfwx_station_list_mapper)

    station_code_dict = {station.wfwx_id: station.code for station in stations}

    for hourly in hourlies:
        if hourly.get('hourlyMeasurementTypeCode', '').get('id') == 'ACTUAL':
            parsed_hourly = parse_hourly(hourly)
            try:
                station_code = station_code_dict[(hourly['stationId'])]
                hourly_actual = parse_hourly_actual(station_code, parsed_hourly)
                if hourly_actual is not None:
                    hourly_actuals.append(hourly_actual)
            except KeyError as exception:
                logger.warning("Missing hourly for station code", exc_info=exception)
    return hourly_actuals


async def get_wfwx_stations_from_station_codes(session, header, station_codes: Optional[List[int]]):
    """ Return the WFWX station ids from WFWX API given a list of station codes. """

    # All WFWX stations are requested because WFWX returns a malformed JSON response when too
    # many station codes are added as query parameters.
    wfwx_stations = await get_stations(session, header, mapper=wfwx_station_list_mapper)

    # Default to all known WFWX station ids if no station codes are specified
    if station_codes is None:
        return list(filter(lambda x: (x.code in get_fire_centre_station_codes()),
                           wfwx_stations))
    requested_stations = []
    station_code_dict = {station.code: station for station in wfwx_stations}
    for station_code in station_codes:
        wfwx_station = station_code_dict.get(station_code)
        if wfwx_station is not None:
            requested_stations.append(wfwx_station)
        else:
            logger.error("No WFWX station id for station code: %s", station_code)

    return requested_stations


async def get_dailies(
        session: ClientSession,
        header: dict,
        wfwx_stations: List[WFWXWeatherStation],
        start_timestamp: int,
        end_timestamp: int) -> List[StationDaily]:
    """ Get the daily actuals for the given station ids.
    """
    wfwx_station_ids = [wfwx_station.wfwx_id for wfwx_station in wfwx_stations]
    dailies_iterator = fetch_paged_response_generator(
        session, header, BuildQueryDailesByStationCode(
            start_timestamp,
            end_timestamp, wfwx_station_ids), 'dailies')

    dailies = []
    station_code_dict = {station.wfwx_id: station.code for station in wfwx_stations}
    async for raw_daily in dailies_iterator:
        wfwx_id = raw_daily.get('stationId', None)
        station_code = station_code_dict.get(wfwx_id, None)
        daily = parse_daily(raw_daily, station_code)
        dailies.append(daily)
    return dailies
