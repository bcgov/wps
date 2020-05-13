""" This module contains methods for retrieving information from the WFWX Fireweather API.
"""
import json
from abc import abstractmethod, ABC
import logging
from typing import List
from aiohttp import ClientSession, BasicAuth
from schemas import WeatherStation
import config

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class BuildUrl(ABC):
    """ Base class for building urls """

    def __init__(self):
        """ Initialize object """
        self.max_page_size = config.get('WFWX_MAX_PAGE_SIZE')
        self.base_url = config.get('WFWX_BASE_URL')

    @abstractmethod
    def url(self, page) -> str:
        """ Return query url """


# pylint: disable=too-few-public-methods
class BuildUrlAllStations(BuildUrl):
    """ Class for building a url to request all stations.  """

    def url(self, page) -> str:
        """ Return query url """
        return '{base_url}/v1/stations?size={size}&sort=displayLabel&page={page}'.format(
            base_url=self.base_url, size=self.max_page_size, page=page)


# pylint: disable=too-few-public-methods
class BuildUrlByStationCode(BuildUrl):
    """ Class for building a url to request a list of stations by code """

    def __init__(self, station_codes: List[int]):
        """ Initialize object """
        super().__init__()
        self.query = ''
        for code in station_codes:
            if len(self.query) > 0:
                self.query += ' or '
            self.query += 'stationCode=={}'.format(code)

    def url(self, page) -> str:
        """ Return query url for a list of stations """
        return '{base_url}/v1/stations/rsql?size={size}&sort=displayLabel&page={page}&query={query}'.format(
            base_url=self.base_url, size=self.max_page_size, page=page, query=self.query)


async def _fetch_access_token(session: ClientSession) -> dict:
    """ Fetch an access token for WFWX Fireweather API
    """
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


async def _fetch_raw_stations(session: ClientSession, headers: dict, url_builder: BuildUrl) -> dict:
    """ Asynchronous generator for iterating through raw stations from the API.
    The station list is a paged response, but this generator abstracts that away.
    """
    # We don't know how many pages until our first call - so we assume one page to start with.
    total_pages = 1
    page_count = 0
    while page_count < total_pages:
        # Build up the request URL.
        url = url_builder.url(page_count)
        LOGGER.debug('loading station page %d...', page_count)
        async with session.get(url, headers=headers) as response:
            station_json = await response.json()
            LOGGER.debug('done loading station page %d.', page_count)
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
        return False
    return True


def _parse_station(station) -> WeatherStation:
    """ Transform from the json object returned by wf1, to our station object.
    """
    return WeatherStation(
        code=station['stationCode'],
        name=station['displayLabel'],
        lat=station['latitude'],
        long=station['longitude'])


def _get_stations_by_codes_local(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from local json files. """
    LOGGER.info('Using pre-generated json to retrieve station by code')
    with open('data/weather_stations.json') as file_pointer:
        stations = json.load(file_pointer)
        results = []
        for station in stations['weather_stations']:
            if int(station['code']) in station_codes:
                results.append(WeatherStation(**station))
        return results


async def _get_stations_by_codes_remote(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    LOGGER.info('Using WFWX to retrieve stations by code')
    async with ClientSession() as session:
        # Get the authentication header
        header = await _get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        iterator = _fetch_raw_stations(
            session, header, BuildUrlByStationCode(station_codes))
        async for raw_station in iterator:
            # If the station is valid, add it to our list of stations.
            if _is_station_valid(raw_station):
                stations.append(_parse_station(raw_station))
        LOGGER.debug('total stations: %d', len(stations))
        return stations


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    use_wfwx = config.get('USE_WFWX') == 'True'
    if use_wfwx:
        return await _get_stations_by_codes_remote(station_codes)
    return _get_stations_by_codes_local(station_codes)


def _get_stations_local() -> List[WeatherStation]:
    """ Get list of stations from local json files.
    """
    LOGGER.info('Using pre-generated json to retrieve station list')
    with open('data/weather_stations.json') as weather_stations_file:
        json_data = json.load(weather_stations_file)
        return json_data['weather_stations']


async def _get_stations_remote() -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    LOGGER.info('Using WFWX to retrieve station list')
    async with ClientSession() as session:
        # Get the authentication header
        header = await _get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        async for raw_station in _fetch_raw_stations(session, header, BuildUrlAllStations()):
            # If the station is valid, add it to our list of stations.
            if _is_station_valid(raw_station):
                stations.append(_parse_station(raw_station))
        LOGGER.debug('total stations: %d', len(stations))
    return stations


async def get_stations() -> List[WeatherStation]:
    """ Get list of stations from WFWX Fireweather API.
    """
    # Check if we're really using the api, or loading from pre-generated files.
    use_wfwx = config.get('USE_WFWX') == 'True'
    if use_wfwx:
        return await _get_stations_remote()
    return _get_stations_local()
