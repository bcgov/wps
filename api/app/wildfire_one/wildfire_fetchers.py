""" Functions that request and marshall WFWX API responses into our schemas"""

import math
import logging
from datetime import datetime
from typing import Dict, Generator, Tuple
from aiohttp.client import ClientSession, BasicAuth
from app.schemas.observations import WeatherStationHourlyReadings
from app.schemas.stations import (DetailedWeatherStationProperties,
                                  GeoJsonDetailedWeatherStation,
                                  WeatherStationGeometry)
from app.db.crud.stations import _get_noon_date
from app.wildfire_one.query_builders import BuildQuery
from app import config
from app.wildfire_one.schema_parsers import _parse_hourly, _parse_station
from app.wildfire_one.util import _is_station_valid

logger = logging.getLogger(__name__)


async def _fetch_paged_response_generator(
        session: ClientSession,
        headers: dict,
        query_builder: BuildQuery,
        content_key: str
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
        async with session.get(url, headers=headers, params=params) as response:
            response_json = await response.json()
            logger.debug('done loading station page %d.', page_count)

        # Update the total page count.
        total_pages = response_json['page']['totalPages'] if 'page' in response_json else 1
        for response_object in response_json['_embedded'][content_key]:
            yield response_object
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


async def _fetch_access_token(session: ClientSession) -> dict:
    """ Fetch an access token for WFWX Fireweather API
    """
    logger.debug('fetching access token...')
    password = config.get('WFWX_SECRET')
    user = config.get('WFWX_USER')
    auth_url = config.get('WFWX_AUTH_URL')
    async with session.get(auth_url, auth=BasicAuth(login=user, password=password)) as response:
        return await response.json()
