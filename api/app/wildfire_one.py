""" This module contains methods for retrieving information from the WFWX Fireweather API.
"""
import os
import json
from datetime import datetime, timedelta, timezone
import math
from abc import abstractmethod, ABC
import logging
from typing import List
import asyncio
import geopandas
from aiohttp import ClientSession, BasicAuth, TCPConnector
from shapely.geometry import Point
from app import config
from app.schemas.observations import WeatherStationHourlyReadings, WeatherReading
from app.schemas.stations import WeatherStation
import app.time_utils


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
        self.max_page_size = config.get('WFWX_MAX_PAGE_SIZE')
        self.base_url = config.get('WFWX_BASE_URL')

    @abstractmethod
    def query(self, page) -> [str, dict]:
        """ Return query url and params """


class BuildQueryAllStations(BuildQuery):
    """ Class for building a url and params to request all stations.  """

    def query(self, page) -> [str, dict]:
        """ Return query url and params """
        params = {'size': self.max_page_size,
                  'sort': 'displayLabel', 'page': page}
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


async def _get_auth_header(session: ClientSession) -> dict:
    # Fetch access token
    token = await _fetch_access_token(session)
    # Construct the header.
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    return header


async def _fetch_raw_stations(session: ClientSession, headers: dict, query_builder: BuildQuery) -> dict:
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
            station_json = await response.json()
            logger.debug('done loading station page %d.', page_count)
        # Update the total page count.
        total_pages = station_json['page']['totalPages']
        for station in station_json['_embedded']['stations']:
            yield station
        # Keep track of our page count.
        page_count = page_count + 1


def _is_station_valid(station) -> bool:
    """ Run through a set of conditions to check if the station is valid.

    Returns True if station is good, False is station is bad.
    """
    if station['stationStatus']['id'] != 'ACTIVE':
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
    with open(core_season_file_path) as file_handle:
        core_seasons = json.load(file_handle)
    ecodivisions = geopandas.read_file(ecodiv_shape_file_path)
    station_coord = Point(
        float(station['longitude']), float(station['latitude']))

    # hacky fix for station 447 (WATSON LAKE FS), which is in the Yukon
    # so ecodivision name has to be hard-coded
    if station['stationCode'] == '447':
        ecodiv_name = "SUB-ARCTIC HIGHLANDS"
    else:
        for index, row in ecodivisions.iterrows():  # pylint: disable=redefined-outer-name, unused-variable
            geom = row['geometry']
            if station_coord.within(geom):
                ecodiv_name = row['CDVSNNM']
                break
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
        ffmc=hourly.get('ffmc', None),
        isi=hourly.get('isi', None),
        fwi=hourly.get('fwi', None)
    )


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    logger.info('Using WFWX to retrieve stations by code')
    async with ClientSession() as session:
        # Get the authentication header
        header = await _get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        iterator = _fetch_raw_stations(
            session, header, BuildQueryByStationCode(station_codes))
        async for raw_station in iterator:
            # If the station is valid, add it to our list of stations.
            if _is_station_valid(raw_station):
                stations.append(_parse_station(raw_station))
        logger.debug('total stations: %d', len(stations))
        return stations


async def get_stations() -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    logger.info('Using WFWX to retrieve station list')
    async with ClientSession() as session:
        # Get the authentication header
        header = await _get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        async for raw_station in _fetch_raw_stations(session, header, BuildQueryAllStations()):
            # If the station is valid, add it to our list of stations.
            if _is_station_valid(raw_station):
                logger.info('Processing raw_station %d',
                            int(raw_station['stationCode']))
                stations.append(_parse_station(raw_station))
        logger.debug('total stations: %d', len(stations))
    return stations


def prepare_fetch_hourlies_query(raw_station: dict, time_of_interest: datetime):
    """ Prepare url and params to fetch hourly readings from the WFWX Fireweather API.
    """
    base_url = config.get('WFWX_BASE_URL')

    # By default we're concerned with the last 5 days only.
    five_days_past = time_of_interest - timedelta(days=5)

    logger.debug('requesting historic data from %s to %s', five_days_past, time_of_interest)

    # Prepare query params and query:
    start_time_stamp = math.floor(five_days_past.timestamp()*1000)
    end_time_stamp = math.floor(time_of_interest.timestamp()*1000)
    station_id = raw_station['id']
    params = {'startTimestamp': start_time_stamp,
              'endTimestamp': end_time_stamp, 'stationId': station_id}
    endpoint = ('/v1/hourlies/search/'
                'findHourliesByWeatherTimestampBetweenAndStationIdEqualsOrderByWeatherTimestampAsc')
    url = '{base_url}{endpoint}'.format(
        base_url=base_url,
        endpoint=endpoint)

    return url, params


async def fetch_hourlies(
        session: ClientSession,
        raw_station: dict,
        headers: dict,
        time_of_interest: datetime) -> WeatherStationHourlyReadings:
    """ Fetch hourly weather readings for a give station.
    """
    logger.debug('fetching hourlies for %s(%s)',
                 raw_station['displayLabel'], raw_station['stationCode'])

    url, params = prepare_fetch_hourlies_query(raw_station, time_of_interest)

    # Get hourlies
    async with session.get(url, params=params, headers=headers) as response:
        hourlies_json = await response.json()
        hourlies = []
        for hourly in hourlies_json['_embedded']['hourlies']:
            # We only accept "ACTUAL" values:
            if hourly.get('hourlyMeasurementTypeCode', '').get('id') == 'ACTUAL':
                hourlies.append(_parse_hourly(hourly))

        logger.debug('fetched %d hourlies for %s(%s)', len(
            hourlies), raw_station['displayLabel'], raw_station['stationCode'])

        return WeatherStationHourlyReadings(values=hourlies, station=_parse_station(raw_station))


async def get_hourly_readings(station_codes: List[int], time_of_interest: datetime) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    """
    # Create a list containing all the tasks to run in parallel.
    tasks = []

    # Limit the number of concurrent connections.
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as session:
        # Get the authentication header
        header = await _get_auth_header(session)

        # Iterate through "raw" station data.
        iterator = _fetch_raw_stations(
            session, header, BuildQueryByStationCode(station_codes))
        async for raw_station in iterator:
            task = asyncio.create_task(
                fetch_hourlies(session, raw_station, header, time_of_interest))
            tasks.append(task)

        # Run the tasks concurrently, waiting for them all to complete.
        return await asyncio.gather(*tasks)
