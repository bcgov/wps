""" Redis cache wrapper for hydrates fire centres """

from functools import reduce
import hashlib
import json
import logging
from typing import List, Optional
from app.schemas.hfi_calc import CachedFireCentres, FireCentre
from app.utils.redis import create_redis

logger = logging.getLogger(__name__)
cache_expiry_seconds = 86400
namespace_prefix = "fire_centres"

# we can safely cache the fire centres, as they don't change them very often.
# the eco-division logic is very slow, and chomps up 2 seconds!


async def get_cached_hydrated_fire_centres(station_codes: List[int]) -> Optional[List[FireCentre]]:
    """ Optionally returns cached fire centres if they exist. """
    key = key_from_station_codes(station_codes)
    cache = create_redis()
    try:
        cached_json = cache.get(key)
    except Exception as error:  # pylint: disable=broad-except
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        logger.info('redis cache hit %s', key)
        cache_string = json.loads(json.loads(cached_json))
        cached_fire_centres: CachedFireCentres = CachedFireCentres(**cache_string)
        return cached_fire_centres.fire_centres

    logger.info('redis cache miss %s', key)
    return None


async def put_cached_hydrated_fire_centres(fire_centres: List[FireCentre]):
    """ Caches fire centres that are assumed to be hydrated by caller. """
    planning_areas = reduce(list.__add__, [fire_centre.planning_areas for fire_centre in fire_centres])
    stations = reduce(list.__add__, [planning_area.stations for planning_area in planning_areas])
    station_codes = [station.code for station in stations]
    key = key_from_station_codes(station_codes)

    to_cache: CachedFireCentres = CachedFireCentres(fire_centres=fire_centres)
    cache = create_redis()
    try:
        cache.set(key, json.dumps(to_cache.json()).encode(), ex=cache_expiry_seconds)
    except Exception as error:  # pylint: disable=broad-except
        logger.error(error, exc_info=error)


def clear_fire_centre_namespace():
    """ Delete any key that starts with the fire_centre prefix """
    cache = create_redis()
    for key in cache.scan_iter(f'{namespace_prefix}*'):
        cache.delete(key)


def key_from_station_codes(station_codes: List[int]) -> str:
    """ Creates a unique hash digest based on station codes that can be changed by user. """
    string_station_codes = list(map(str, sorted(station_codes)))
    data_key = str.encode(''.join(string_station_codes), 'utf-8')
    hash_key = hashlib.sha3_512(data_key).hexdigest()
    return f'{namespace_prefix}-{hash_key}'
