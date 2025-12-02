""" Central location to instantiate redis for easier mocking in unit tests.
"""
from redis import StrictRedis
from wps_shared import config


def _create_redis():
    return StrictRedis(host=config.get('REDIS_HOST'),
                       port=config.get('REDIS_PORT', 6379),
                       db=0,
                       password=config.get('REDIS_PASSWORD'))


def create_redis():
    """ Call _create_redis, to make it easy to mock out for everyone in unit testing. """
    return _create_redis()


def clear_cache_matching(key_part_match: str):
    """
    Clear cache entry from redis cache

    :param key_part_match: Part of key to search for in redis key
    :type key_match_str: str
    """
    redis = create_redis()
    for key in redis.scan_iter(f'*{key_part_match}*'):
        redis.delete(key)
