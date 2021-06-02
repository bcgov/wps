""" This module contains methods for retrieving information from the WFWX Fireweather API.
"""
import os
import json
import math
from typing import Generator, Dict, List
from datetime import datetime, timezone
from abc import abstractmethod, ABC
import logging
import asyncio
import geopandas
from aiohttp import ClientSession, BasicAuth, TCPConnector
from shapely.geometry import Point
from app import config
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherStationHourlyReadings, WeatherReading
from app.schemas.stations import (WeatherStation, GeoJsonDetailedWeatherStation,
                                  DetailedWeatherStationProperties, WeatherStationGeometry, WeatherVariables)
from app.db.crud.stations import _get_noon_date


logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
core_season_file_path = os.path.join(
    dirname, 'data/ecodivisions_core_seasons.json')
ecodiv_shape_file_path = os.path.join(
    dirname, 'data/ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')


class BuildQuery(ABC):
    """ Base class for building query urls and params """

    def __init__(self):
        """ Initialize object """
        self.max_page_size = config.get('WFWX_MAX_PAGE_SIZE', 1000)
        self.base_url = config.get('WFWX_BASE_URL')

    @abstractmethod
    def query(self, page) -> [str, dict]:
        """ Return query url and params """


class BuildQueryAllActiveStations(BuildQuery):
    """ Class for building a url and RSQL params to request all active stations. """

    def query(self, page) -> [str, dict]:
        """ Return query url and params with rsql query for all weather stations marked active. """
        # NOTE: Currently the filter on stationStatus.id doesn't work.
        params = {'size': self.max_page_size, 'sort': 'displayLabel',
                  'page': page, 'query': 'stationStatus.id=="ACTIVE"'}
        url = '{base_url}/v1/stations'.format(base_url=self.base_url)
        return [url, params]


class BuildQueryByStationCode(BuildQuery):
    """ Class for building a url and params to request a list of stations by code """

    def __init__(self, station_codes: List[int]):
        """ Initialize object """
        super().__init__()
        self.querystring = ''
        for code in station_codes:
            if len(self.querystring) > 0:
                self.querystring += ' or '
            self.querystring += 'stationCode=={}'.format(code)

    def query(self, page) -> [str, dict]:
        """ Return query url and params for a list of stations """
        params = {'size': self.max_page_size,
                  'sort': 'displayLabel', 'page': page, 'query': self.querystring}
        url = '{base_url}/v1/stations/rsql'.format(base_url=self.base_url)
        return [url, params]


def use_wfwx():
    """ Return True if configured to use WFWX """
    using_wfwx = config.get('USE_WFWX') == 'True'
    logger.info('USE_WFWX = %s', using_wfwx)
    return using_wfwx


async def _fetch_access_token(session: ClientSession) -> dict:
    """ Fetch an access token for WFWX Fireweather API
    """
    logger.debug('fetching access token...')
    password = config.get('WFWX_SECRET')
    user = config.get('WFWX_USER')
    auth_url = config.get('WFWX_AUTH_URL')
    async with session.get(auth_url, auth=BasicAuth(login=user, password=password)) as response:
        return await response.json()


async def get_auth_header(session: ClientSession) -> dict:
    """Get WFWX auth header"""
    # Fetch access token
    token = await _fetch_access_token(session)
    # Construct the header.
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    return header


async def _fetch_raw_stations_generator(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery) -> Generator[dict, None, None]:
    """ Asynchronous generator for iterating through raw stations from the API.
    The station list is a paged response, but this generator abstracts that away.
    """
    # We don't know how many pages until our first call - so we assume one page to start with.
    total_pages = 1
    page_count = 0
    while page_count < total_pages:
        # Build up the request URL.
        url, params = query_builder.query(page_count)
        logger.debug('loading station page %d...', page_count)
        async with session.get(url, headers=headers, params=params) as response:
            response_bytes = await response.read()
            logger.debug('done loading station page %d.', page_count)

        station_json = json.loads(response_bytes.decode('utf-8'))
        # Update the total page count.
        total_pages = station_json['page']['totalPages']
        for station in station_json['_embedded']['stations']:
            yield station
        # Keep track of our page count.
        page_count = page_count + 1


async def _fetch_detailed_geojson_stations(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery) -> (Dict[int, GeoJsonDetailedWeatherStation], Dict[str, int]):
    stations = {}
    id_to_code_map = {}
    # Put the stations in a nice dictionary.
    async for raw_station in _fetch_raw_stations_generator(session, headers, query_builder):
        station_code = raw_station.get('stationCode')
        station_status = raw_station.get('stationStatus', {}).get('id')
        # Because we can't filter on status in the RSQL, we have to manually exclude stations that are
        # not active.
        if _is_station_valid(raw_station):
            id_to_code_map[raw_station.get('id')] = station_code
            geojson_station = GeoJsonDetailedWeatherStation(properties=DetailedWeatherStationProperties(
                code=station_code,
                name=raw_station.get('displayLabel')),
                geometry=WeatherStationGeometry(
                    coordinates=[raw_station.get('longitude'), raw_station.get('latitude')]))
            stations[station_code] = geojson_station
        else:
            logger.debug('station %s, status %s', station_code, station_status)

    return stations, id_to_code_map


def _is_station_valid(station) -> bool:
    """ Run through a set of conditions to check if the station is valid.

    The RSQL filter is unable to filter on station status.

    Returns True if station is good, False is station is bad.
    """
    # In conversation with Dana Hicks, on Apr 20, 2021 - Dana said to show active, test and project.
    if not station.get('stationStatus', {}).get('id') in ('ACTIVE', 'TEST', 'PROJECT'):
        return False
    if station['latitude'] is None or station['longitude'] is None:
        # We can't use a station if it doesn't have a latitude and longitude.
        # pylint: disable=fixme
        # TODO : Decide if a station is valid if we can't determine its ecodivision and/or core fire season
        return False
    return True


def _parse_station(station) -> WeatherStation:
    """ Transform from the json object returned by wf1, to our station object.
    """
    # pylint: disable=no-member
    core_seasons = EcodivisionSeasons.instance().get_core_seasons()
    ecodiv_name = EcodivisionSeasons.instance().get_ecodivision_name(
        station['latitude'], station['longitude'])
    return WeatherStation(
        code=station['stationCode'],
        name=station['displayLabel'],
        lat=station['latitude'],
        long=station['longitude'],
        ecodivision_name=ecodiv_name,
        core_season=core_seasons[ecodiv_name]['core_season'])


def _parse_hourly(hourly) -> WeatherReading:
    """ Transform from the raw hourly json object returned by wf1, to our hourly obkect.
    """
    timestamp = datetime.fromtimestamp(
        int(hourly['weatherTimestamp'])/1000, tz=timezone.utc).isoformat()
    return WeatherReading(
        datetime=timestamp,
        temperature=hourly.get('temperature', None),
        relative_humidity=hourly.get('relativeHumidity', None),
        wind_speed=hourly.get('windSpeed', None),
        wind_direction=hourly.get('windDirection', None),
        barometric_pressure=hourly.get('barometricPressure', None),
        precipitation=hourly.get('precipitation', None),
        ffmc=hourly.get('fineFuelMoistureCode', None),
        isi=hourly.get('initialSpreadIndex', None),
        fwi=hourly.get('fireWeatherIndex', None),
        observation_valid_ind=hourly.get('observationValidInd'),
        observation_valid_comment=hourly.get('observationValidComment')
    )


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    logger.info('Using WFWX to retrieve stations by code')
    async with ClientSession() as session:
        header = get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        iterator = _fetch_raw_stations_generator(
            session, header, BuildQueryByStationCode(station_codes))
        async for raw_station in iterator:
            # If the station is valid, add it to our list of stations.
            if _is_station_valid(raw_station):
                stations.append(_parse_station(raw_station))
        logger.debug('total stations: %d', len(stations))
        return stations


async def station_list_mapper(raw_stations: Generator[dict, None, None]):
    """ Maps raw stations to WeatherStation list"""
    stations = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if _is_station_valid(raw_station):
            stations.append(WeatherStation(code=raw_station['stationCode'],
                                           name=raw_station['displayLabel'],
                                           lat=raw_station['latitude'],
                                           long=raw_station['longitude']))
    return stations


async def station_codes_list_mapper(raw_stations: Generator[dict, None, None]):
    """ Maps raw stations to station codes"""
    station_codes = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if _is_station_valid(raw_station):
            station_codes.append(raw_station['stationCode'])
    return station_codes


async def get_stations(session: ClientSession,
                       header: dict,
                       mapper=station_list_mapper) -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    logger.info('Using WFWX to retrieve station list')
    # Iterate through "raw" station data.
    raw_stations = _fetch_raw_stations_generator(
        session, header, BuildQueryAllActiveStations())
    # If the station is valid, add it to our list of stations.
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
        stations_task = asyncio.create_task(_fetch_detailed_geojson_stations(
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


def prepare_fetch_hourlies_query(raw_station: dict, start_timestamp: datetime, end_timestamp: datetime):
    """ Prepare url and params to fetch hourly readings from the WFWX Fireweather API.
    """
    base_url = config.get('WFWX_BASE_URL')

    logger.debug('requesting historic data from %s to %s', start_timestamp, end_timestamp)

    # Prepare query params and query:
    query_start_timestamp = math.floor(start_timestamp.timestamp()*1000)
    query_end_timestamp = math.floor(end_timestamp.timestamp()*1000)

    station_id = raw_station['id']
    params = {'startTimestamp': query_start_timestamp,
              'endTimestamp': query_end_timestamp, 'stationId': station_id}
    endpoint = ('/v1/hourlies/search/'
                'findHourliesByWeatherTimestampBetweenAndStationIdEqualsOrderByWeatherTimestampAsc')
    url = '{base_url}{endpoint}'.format(
        base_url=base_url,
        endpoint=endpoint)

    return url, params


def prepare_fetch_dailies_for_all_stations_query(time_of_interest: datetime, page_count: int):
    """ Prepare url and params for fetching dailies (that's forecast and observations for noon) for all.
    stations. """
    base_url = config.get('WFWX_BASE_URL')
    noon_date = _get_noon_date(time_of_interest)
    timestamp = int(noon_date.timestamp()*1000)
    # one could filter on recordType.id==FORECAST or recordType.id==ACTUAL but we want it all.
    params = {'query': f'weatherTimestamp=={timestamp}',
              'page': page_count,
              'size': config.get('WFWX_MAX_PAGE_SIZE', 1000)}
    endpoint = ('/v1/dailies/rsql')
    url = f'{base_url}{endpoint}'
    return url, params


async def fetch_raw_dailies_for_all_stations(
        session: ClientSession, headers: dict, time_of_interest: datetime) -> list:
    """ Fetch the noon values (observations and forecasts) for a given time, for all weather stations.
    """
    # We don't know how many pages until our first call - so we assume one page to start with.
    total_pages = 1
    page_count = 0
    hourlies = []
    while page_count < total_pages:
        # Build up the request URL.
        url, params = prepare_fetch_dailies_for_all_stations_query(time_of_interest, page_count)
        # Get dailies
        async with session.get(url, params=params, headers=headers) as response:
            dailies_json = await response.json()
            total_pages = dailies_json['page']['totalPages']
            hourlies.extend(dailies_json['_embedded']['dailies'])
        page_count = page_count + 1
    return hourlies


async def fetch_hourlies(
        session: ClientSession,
        raw_station: dict,
        headers: dict,
        start_timestamp: datetime,
        end_timestamp: datetime) -> WeatherStationHourlyReadings:
    """ Fetch hourly weather readings for the specified time range for a give station """
    logger.debug('fetching hourlies for %s(%s)',
                 raw_station['displayLabel'], raw_station['stationCode'])

    url, params = prepare_fetch_hourlies_query(raw_station, start_timestamp, end_timestamp)

    # Get hourlies
    async with session.get(url, params=params, headers=headers) as response:
        hourlies_json = await response.json()
        hourlies = []
        for hourly in hourlies_json['_embedded']['hourlies']:
            # We only accept "ACTUAL" values and values that have a dewpoint:
            if hourly.get('hourlyMeasurementTypeCode', '').get('id') == 'ACTUAL':
                hourlies.append(_parse_hourly(hourly))

        logger.debug('fetched %d hourlies for %s(%s)', len(
            hourlies), raw_station['displayLabel'], raw_station['stationCode'])

        return WeatherStationHourlyReadings(values=hourlies, station=_parse_station(raw_station))


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
    iterator = _fetch_raw_stations_generator(
        session, header, BuildQueryByStationCode(station_codes))
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


async def get_hourly_readings_all_stations(
        session: ClientSession,
        header: dict,
        start_timestamp: datetime,
        end_timestamp: datetime) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    """
    # Create a list containing all the tasks to run in parallel.
    tasks = []

    # Iterate through "raw" station data.
    iterator = _fetch_raw_stations_generator(
        session, header, BuildQueryAllActiveStations())
    async for raw_station in iterator:
        if _is_station_valid(raw_station):
            task = asyncio.create_task(
                fetch_hourlies(session,
                               raw_station,
                               header,
                               start_timestamp,
                               end_timestamp))
            tasks.append(task)

    # Run the tasks concurrently, waiting for them all to complete.
    return await asyncio.gather(*tasks)
