""" Functions that request and marshall WFWX API responses into our schemas"""
import math
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Tuple, Final
import json
from urllib.parse import urlencode
from aiohttp.client import ClientSession, BasicAuth
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.rocketchat_notifications import send_rocketchat_notification
from app.schemas.observations import WeatherStationHourlyReadings
from app.schemas.stations import (DetailedWeatherStationProperties,
                                  GeoJsonDetailedWeatherStation,
                                  WeatherStationGeometry)
from db.crud.stations import _get_noon_date
from app.wildfire_one.query_builders import BuildQuery
from app import config
from app.wildfire_one.schema_parsers import parse_hourly, parse_station
from app.wildfire_one.util import is_station_valid
from app.utils.redis import create_redis

logger = logging.getLogger(__name__)


async def _fetch_cached_response(session: ClientSession, headers: dict, url: str, params: dict,
                                 cache_expiry_seconds: int):
    cache = create_redis()
    key = f'{url}?{urlencode(params)}'
    try:
        cached_json = cache.get(key)
    except Exception as error:  # pylint: disable=broad-except
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        logger.info('redis cache hit %s', key)
        response_json = json.loads(cached_json.decode())
    else:
        logger.info('redis cache miss %s', key)
        async with session.get(url, headers=headers, params=params) as response:
            try:
                response_json = await response.json()
            except json.decoder.JSONDecodeError as error:
                logger.error(error, exc_info=error)
                text = await response.text()
                logger.error('response.text() = %s', text)
                send_rocketchat_notification(f'JSONDecodeError, response.text() = {text}', error)
                raise
        try:
            if response.status == 200:
                cache.set(key, json.dumps(response_json).encode(), ex=cache_expiry_seconds)
        except Exception as error:  # pylint: disable=broad-except
            logger.error(error, exc_info=error)
    return response_json


async def fetch_paged_response_generator(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery,
        content_key: str,
        use_cache: bool = False,
        cache_expiry_seconds: int = 86400
) -> AsyncGenerator[dict, None]:
    """ Asynchronous generator for iterating through responses from the API.
    The response is a paged response, but this generator abstracts that away.
    """
    # We don't know how many pages until our first call - so we assume one page to start with.
    total_pages = 1
    page_count = 0
    while page_count < total_pages:
        # Build up the request URL.
        url, params = query_builder.query(page_count)
        logger.debug('loading page %d...', page_count)
        if use_cache and config.get('REDIS_USE') == 'True':
            # We've been told and configured to use the redis cache.
            response_json = await _fetch_cached_response(session, headers, url, params, cache_expiry_seconds)
        else:
            async with session.get(url, headers=headers, params=params) as response:
                response_json = await response.json()
                logger.debug('done loading page %d.', page_count)

        # keep this code around for dumping responses to a json file - useful for when you're writing
        # tests to grab actual responses to use in fixtures.
        # import base64
        # TODO: write a beter way to make a temporary filename
        # fname = 'thing_{}_{}.json'.format(base64.urlsafe_b64encode(url.encode()), random.randint(0, 1000))
        # with open(fname, 'w') as f:
        #     json.dump(response_json, f)

        # Update the total page count.
        total_pages = response_json['page']['totalPages'] if 'page' in response_json else 1
        for response_object in response_json['_embedded'][content_key]:
            yield response_object
        # Keep track of our page count.
        page_count = page_count + 1


async def fetch_detailed_geojson_stations(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery) -> Tuple[Dict[int, GeoJsonDetailedWeatherStation], Dict[str, int]]:
    """ Fetch and marshall geojson station data"""
    stations = {}
    id_to_code_map = {}
    # 1 week seems a reasonable period to cache stations for.
    redis_station_cache_expiry: Final = int(config.get('REDIS_STATION_CACHE_EXPIRY', 604800))
    # Put the stations in a nice dictionary.
    async for raw_station in fetch_paged_response_generator(session,
                                                            headers,
                                                            query_builder,
                                                            'stations',
                                                            True,
                                                            redis_station_cache_expiry):
        station_code = raw_station.get('stationCode')
        station_status = raw_station.get('stationStatus', {}).get('id')
        # Because we can't filter on status in the RSQL, we have to manually exclude stations that are
        # not active.
        if is_station_valid(raw_station):
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


def prepare_fetch_hourlies_query(raw_station: dict, start_timestamp: datetime, end_timestamp: datetime):
    """ Prepare url and params to fetch hourly readings from the WFWX Fireweather API.
    """
    base_url = config.get('WFWX_BASE_URL')

    logger.debug('requesting historic data from %s to %s', start_timestamp, end_timestamp)

    # Prepare query params and query:
    query_start_timestamp = math.floor(start_timestamp.timestamp() * 1000)
    query_end_timestamp = math.floor(end_timestamp.timestamp() * 1000)

    station_id = raw_station['id']
    params = {'startTimestamp': query_start_timestamp,
              'endTimestamp': query_end_timestamp, 'stationId': station_id}
    endpoint = ('/v1/hourlies/search/'
                'findHourliesByWeatherTimestampBetweenAndStationIdEqualsOrderByWeatherTimestampAsc')
    url = f'{base_url}{endpoint}'

    return url, params


def prepare_fetch_dailies_for_all_stations_query(time_of_interest: datetime, page_count: int):
    """ Prepare url and params for fetching dailies(that's forecast and observations for noon) for all.
    stations. """
    base_url = config.get('WFWX_BASE_URL')
    noon_date = _get_noon_date(time_of_interest)
    timestamp = int(noon_date.timestamp() * 1000)
    # one could filter on recordType.id==FORECAST or recordType.id==ACTUAL but we want it all.
    params = {'query': f'weatherTimestamp=={timestamp}',
              'page': page_count,
              'size': config.get('WFWX_MAX_PAGE_SIZE', 1000)}
    endpoint = ('/v1/dailies/rsql')
    url = f'{base_url}{endpoint}'
    logger.info('%s         %s', url, params)
    return url, params


async def fetch_hourlies(
        session: ClientSession,
        raw_station: dict,
        headers: dict,
        start_timestamp: datetime,
        end_timestamp: datetime,
        use_cache: bool,
        eco_division: EcodivisionSeasons) -> WeatherStationHourlyReadings:
    """ Fetch hourly weather readings for the specified time range for a give station """
    logger.debug('fetching hourlies for %s(%s)',
                 raw_station['displayLabel'], raw_station['stationCode'])

    url, params = prepare_fetch_hourlies_query(raw_station, start_timestamp, end_timestamp)

    cache_expiry_seconds: Final = int(config.get('REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY', 300))

    # Get hourlies
    if use_cache and cache_expiry_seconds is not None and config.get('REDIS_USE') == 'True':
        hourlies_json = await _fetch_cached_response(session, headers, url, params, cache_expiry_seconds)
    else:
        async with session.get(url, params=params, headers=headers) as response:
            hourlies_json = await response.json()

    hourlies = []
    for hourly in hourlies_json['_embedded']['hourlies']:
        # We only accept "ACTUAL" values
        if hourly.get('hourlyMeasurementTypeCode', '').get('id') == 'ACTUAL':
            hourlies.append(parse_hourly(hourly))

    logger.debug('fetched %d hourlies for %s(%s)', len(
        hourlies), raw_station['displayLabel'], raw_station['stationCode'])

    return WeatherStationHourlyReadings(values=hourlies,
                                        station=parse_station(
                                            raw_station, eco_division))


async def fetch_access_token(session: ClientSession) -> dict:
    """ Fetch an access token for WFWX Fireweather API
    """
    logger.debug('fetching access token...')
    password = config.get('WFWX_SECRET')
    user = config.get('WFWX_USER')
    auth_url = config.get('WFWX_AUTH_URL')
    cache = create_redis()
    # NOTE: Consider using a hashed version of the password as part of the key.
    params = {'user': user}
    key = f'{auth_url}?{urlencode(params)}'
    try:
        cached_json = cache.get(key)
    except Exception as error:  # pylint: disable=broad-except
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        logger.info('redis cache hit %s', auth_url)
        response_json = json.loads(cached_json.decode())
    else:
        logger.info('redis cache miss %s', auth_url)
        async with session.get(auth_url, auth=BasicAuth(login=user, password=password)) as response:
            response_json = await response.json()
            try:
                if response.status == 200:
                    # We expire when the token expires, or 10 minutes, whichever is less.
                    # NOTE: only caching for 10 minutes right now, since we aren't handling cases
                    # where the token is invalidated.
                    redis_auth_cache_expiry: Final = int(config.get('REDIS_AUTH_CACHE_EXPIRY', 600))
                    expires = min(response_json['expires_in'], redis_auth_cache_expiry)
                    cache.set(key, json.dumps(response_json).encode(), ex=expires)
            except Exception as error:  # pylint: disable=broad-except
                logger.error(error, exc_info=error)
    return response_json
