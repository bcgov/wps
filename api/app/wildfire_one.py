""" This module contains methods for retrieving information from the WFWX Fireweather API.
"""
import math
from typing import Generator, Dict, List, Tuple, Final
from datetime import datetime, timezone
from abc import abstractmethod, ABC
import json
import logging
import asyncio
from urllib.parse import urlencode
from aiohttp import ClientSession, BasicAuth, TCPConnector
from redis import StrictRedis
from app import config
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.db.models.observations import HourlyActual
from app.schemas.observations import WeatherStationHourlyReadings, WeatherReading
from app.schemas.stations import (WeatherStation, GeoJsonDetailedWeatherStation,
                                  DetailedWeatherStationProperties, WeatherStationGeometry, WeatherVariables)
from app.db.crud.stations import _get_noon_date
from app.utils.dewpoint import compute_dewpoint


logger = logging.getLogger(__name__)


class BuildQuery(ABC):
    """ Base class for building query urls and params """

    def __init__(self):
        """ Initialize object """
        self.max_page_size = config.get('WFWX_MAX_PAGE_SIZE', 1000)
        self.base_url = config.get('WFWX_BASE_URL')

    @abstractmethod
    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params """


class BuildQueryAllActiveStations(BuildQuery):
    """ Class for building a url and RSQL params to request all active stations. """

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params with rsql query for all weather stations marked active. """
        # NOTE: Currently the filter on stationStatus.id doesn't work.
        params = {'size': self.max_page_size, 'sort': 'displayLabel',
                  'page': page, 'query': 'stationStatus.id=="ACTIVE"'}
        url = '{base_url}/v1/stations'.format(base_url=self.base_url)
        return url, params


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

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params for a list of stations """
        params = {'size': self.max_page_size,
                  'sort': 'displayLabel', 'page': page, 'query': self.querystring}
        url = '{base_url}/v1/stations/rsql'.format(base_url=self.base_url)
        return url, params


class BuildQueryAllHourliesByRange(BuildQuery):
    """ Builds query for requesting all hourlies in a time range"""

    def __init__(self, start_timestamp: int, end_timestamp: int):
        """ Initialize object """
        super().__init__()
        self.querystring: str = "weatherTimestamp >=" + \
            str(start_timestamp) + ";" + "weatherTimestamp <" + str(end_timestamp)

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url for hourlies between start_timestamp, end_timestamp"""
        params = {'size': self.max_page_size, 'page': page, 'query': self.querystring}
        url = '{base_url}/v1/hourlies/rsql'.format(
            base_url=self.base_url)
        return url, params


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


async def _fetch_cached_response(session: ClientSession, headers: dict, url: str, params: dict,
                                 cache_expiry_seconds: int):
    cache = StrictRedis(host=config.get('REDIS_HOST'),
                        port=config.get('REDIS_PORT', 6379),
                        db=0,
                        password=config.get('REDIS_PASSWORD'))

    key = f'{url}?{urlencode(params)}'
    try:
        cached_json = cache.get(key)
    except Exception as error:  # pylint: disable=broad-except
        cached_json = None
        logger.error(error)
    if cached_json:
        logger.info('redis cache hit')
        response_json = json.loads(cached_json.decode())
    else:
        logger.info('cache miss')
        async with session.get(url, headers=headers, params=params) as response:
            response_json = await response.json()
        try:
            cache.set(key, json.dumps(response_json).encode(), ex=cache_expiry_seconds)
        except Exception as error:  # pylint: disable=broad-except
            logger.error(error)
    return response_json


async def _fetch_paged_response_generator(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery,
        content_key: str,
        use_cache: bool = False,
        cache_expiry_seconds: int = 86400
) -> Generator[dict, None, None]:
    """ Asynchronous generator for iterating through responses from the API.
    The response is a paged response, but this generator abstracts that away.
    """
    # We don't know how many pages until our first call - so we assume one page to start with.
    total_pages = 1
    page_count = 0
    while page_count < total_pages:
        # Build up the request URL.
        url, params = query_builder.query(page_count)
        logger.debug('loading station page %d...', page_count)
        if use_cache and config.get('REDIS_USE') == 'True':
            # We've been told and configured to use the redis cache.
            station_json = await _fetch_cached_response(session, headers, url, params, cache_expiry_seconds)
        else:
            async with session.get(url, headers=headers, params=params) as response:
                station_json = await response.json()
            logger.debug('done loading station page %d.', page_count)

        # Update the total page count.
        total_pages = station_json['page']['totalPages']
        for station in station_json['_embedded'][content_key]:
            yield station
        # Keep track of our page count.
        page_count = page_count + 1


async def _fetch_detailed_geojson_stations(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery) -> Tuple[Dict[int, GeoJsonDetailedWeatherStation], Dict[str, int]]:
    stations = {}
    id_to_code_map = {}
    # Put the stations in a nice dictionary.
    async for raw_station in _fetch_paged_response_generator(session, headers, query_builder, 'stations'):
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
        station['stationCode'], station['latitude'], station['longitude'])
    return WeatherStation(
        code=station['stationCode'],
        name=station['displayLabel'],
        lat=station['latitude'],
        long=station['longitude'],
        ecodivision_name=ecodiv_name,
        core_season=core_seasons[ecodiv_name]['core_season'],
        elevation=station['elevation'],
        wfwx_station_uuid=station['id'])


def _parse_hourly(hourly) -> WeatherReading:
    """ Transform from the raw hourly json object returned by wf1, to our hourly object.
    """
    timestamp = datetime.fromtimestamp(
        int(hourly['weatherTimestamp'])/1000, tz=timezone.utc).isoformat()
    return WeatherReading(
        datetime=timestamp,
        temperature=hourly.get('temperature', None),
        relative_humidity=hourly.get('relativeHumidity', None),
        dewpoint=compute_dewpoint(hourly.get('temperature'), hourly.get('relativeHumidity')),
        wind_speed=hourly.get('windSpeed', None),
        wind_direction=hourly.get('windDirection', None),
        barometric_pressure=hourly.get('barometricPressure', None),
        precipitation=hourly.get('precipitation', None),
        ffmc=hourly.get('fineFuelMoistureCode', None),
        isi=hourly.get('initialSpreadIndex', None),
        fwi=hourly.get('fireWeatherIndex', None),
        observation_valid=hourly.get('observationValidInd'),
        observation_valid_comment=hourly.get('observationValidComment')
    )


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """ Get a list of stations by code, from WFWX Fireweather API. """
    logger.info('Using WFWX to retrieve stations by code')
    async with ClientSession() as session:
        header = await get_auth_header(session)
        stations = []
        # Iterate through "raw" station data.
        iterator = _fetch_paged_response_generator(
            session, header, BuildQueryByStationCode(station_codes), 'stations')
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
        if _is_station_valid(raw_station):
            stations.append(WFWXWeatherStation(wfwx_id=raw_station['id'],
                                               code=raw_station['stationCode']))
    return stations


async def get_stations(session: ClientSession,
                       header: dict,
                       mapper=station_list_mapper):
    """ Get list of stations from WFWX Fireweather API.
    """
    logger.info('Using WFWX to retrieve station list')
    # 1 day seems a reasonable period to cache stations for.
    redis_station_cache_expiry: Final = 86400
    # Iterate through "raw" station data.
    raw_stations = _fetch_paged_response_generator(session,
                                                   header,
                                                   BuildQueryAllActiveStations(),
                                                   'stations',
                                                   use_cache=True,
                                                   cache_expiry_seconds=redis_station_cache_expiry)
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
    """ Prepare url and params for fetching dailies(that's forecast and observations for noon) for all.
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
    """ Fetch the noon values(observations and forecasts) for a given time, for all weather stations.
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
            # We only accept "ACTUAL" values
            if hourly.get('hourlyMeasurementTypeCode', '').get('id') == 'ACTUAL':
                hourlies.append(_parse_hourly(hourly))

        logger.error('fetched %d hourlies for %s(%s)', len(
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
    iterator = _fetch_paged_response_generator(
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
    hourlies_iterator = _fetch_paged_response_generator(
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
            parsed_hourly = _parse_hourly(hourly)
            try:
                station_code = station_code_dict[(hourly['stationId'])]
                hourly_actual = parse_hourly_actual(station_code, parsed_hourly)
                if hourly_actual is not None:
                    hourly_actuals.append(hourly_actual)
            except KeyError as exception:
                logger.warning("Missing hourly for station code", exc_info=exception)
    return hourly_actuals


def parse_hourly_actual(station_code: int, hourly_reading: WeatherReading):
    """ Maps WeatherReading to HourlyActual """
    temp_valid = hourly_reading.temperature is not None
    rh_valid = hourly_reading.relative_humidity is not None and validate_metric(
        hourly_reading.relative_humidity, 0, 100)
    wdir_valid = hourly_reading.wind_direction is not None and validate_metric(
        hourly_reading.wind_direction, 0, 360)
    wspeed_valid = hourly_reading.wind_speed is not None and validate_metric(
        hourly_reading.wind_speed, 0, math.inf)
    precip_valid = hourly_reading.precipitation is not None and validate_metric(
        hourly_reading.precipitation, 0, math.inf)

    is_valid_wfwx = hourly_reading.observation_valid
    if is_valid_wfwx is False:
        logger.warning("Invalid hourly received from WF1 API for station code %s at time %s: %s",
                       station_code,
                       hourly_reading.datetime.strftime("%b %d %Y %H:%M:%S"),
                       hourly_reading.observation_valid_comment)

    is_valid = temp_valid and rh_valid and wdir_valid and wspeed_valid and precip_valid and is_valid_wfwx

    return None if (is_valid is False) else HourlyActual(
        station_code=station_code,
        weather_date=hourly_reading.datetime,
        temp_valid=temp_valid,
        temperature=hourly_reading.temperature,
        rh_valid=rh_valid,
        relative_humidity=hourly_reading.relative_humidity,
        wspeed_valid=wspeed_valid,
        wind_speed=hourly_reading.wind_speed,
        wdir_valid=wdir_valid,
        wind_direction=hourly_reading.wind_direction,
        precip_valid=precip_valid,
        precipitation=hourly_reading.precipitation,
        dewpoint=hourly_reading.dewpoint,
        ffmc=hourly_reading.ffmc,
        isi=hourly_reading.isi,
        fwi=hourly_reading.fwi,
    )


def validate_metric(value, low, high):
    """ Validate metric with it's range of accepted values """
    return low <= value <= high
