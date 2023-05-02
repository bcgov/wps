""" Redis cache wrapper for hydrates fire centres
    We can safely cache the fire centres, as they don't change them very often.
    the eco-division logic is very slow, and chomps up 2 seconds!
"""

import json
import logging
from typing import Optional
from app.schemas.hfi_calc import HFIWeatherStationsResponse
from app.utils.redis import create_redis

logger = logging.getLogger(__name__)
cache_expiry_seconds = 86400  # 1 day, 24 hours, 1440 minutes
key = "fire_centres"


async def get_cached_hydrated_fire_centres() -> Optional[HFIWeatherStationsResponse]:
    """ Optionally returns cached fire centres if they exist. """
    cache = create_redis()
    try:
        cached_json = cache.get(key)
    except Exception as error:
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        cache_string = json.loads(cached_json.decode())
        if len(cache_string.get(key)) > 0:
            logger.info('redis cache hit %s', key)
            cached_response: HFIWeatherStationsResponse = HFIWeatherStationsResponse(**cache_string)
            return cached_response

    logger.info('redis cache miss %s', key)
    return None


async def put_cached_hydrated_fire_centres(response: HFIWeatherStationsResponse):
    """ Caches fire centres that are assumed to be hydrated by caller. """
    cache = create_redis()
    try:
        cache.set(key, response.json().encode(), ex=cache_expiry_seconds)
    except Exception as error:
        logger.error(error, exc_info=error)


def clear_cached_hydrated_fire_centres():
    """ Delete the cached value. """
    cache = create_redis()
    cache.delete(key)
