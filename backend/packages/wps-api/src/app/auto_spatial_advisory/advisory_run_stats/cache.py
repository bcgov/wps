"""Redis cache wrappers for advisory run stats (provincial summary, hfi-stats, tpi-stats).

Safe to cache: this data is immutable once an SFMS run completes -- keyed on the run itself
(run_type/run_datetime/for_date), so a new run gets a new key rather than needing invalidation.
"""

import json
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from redis import StrictRedis
from wps_shared import config
from wps_shared.schemas.fba import HFIStatsResponse, ProvincialSummaryResponse, TPIResponse

logger = logging.getLogger(__name__)
cache_expiry_seconds = 86400  # 1 day -- generous since a completed run's data never changes

# A short timeout here still gets caught by the except blocks below, same as any other
# Redis failure, but bounds how long a struggling cache can hold up real traffic.
_REDIS_TIMEOUT_SECONDS = 1


def create_redis():
    return StrictRedis(
        host=config.get("REDIS_HOST"),
        port=config.get("REDIS_PORT", 6379),
        db=0,
        password=config.get("REDIS_PASSWORD"),
        socket_connect_timeout=_REDIS_TIMEOUT_SECONDS,
        socket_timeout=_REDIS_TIMEOUT_SECONDS,
    )


T = TypeVar("T", bound=BaseModel)


def _run_key(prefix: str, run_type: str, run_datetime, for_date) -> str:
    return f"{prefix}_{run_type}_{run_datetime}_{for_date}"


async def _get_cached(key: str, model_cls: Type[T]) -> Optional[T]:
    cache = create_redis()
    try:
        cached_json = cache.get(key)
    except Exception as error:
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        logger.info("redis cache hit %s", key)
        return model_cls(**json.loads(cached_json.decode()))
    logger.info("redis cache miss %s", key)
    return None


async def _put_cached(key: str, response: BaseModel):
    cache = create_redis()
    try:
        cache.set(key, response.model_dump_json().encode(), ex=cache_expiry_seconds)
    except Exception as error:
        logger.error(error, exc_info=error)


async def get_cached_provincial_summary(
    run_type: str, run_datetime, for_date
) -> Optional[ProvincialSummaryResponse]:
    return await _get_cached(
        _run_key("provincial_summary", run_type, run_datetime, for_date), ProvincialSummaryResponse
    )


async def put_cached_provincial_summary(
    run_type: str, run_datetime, for_date, response: ProvincialSummaryResponse
):
    await _put_cached(_run_key("provincial_summary", run_type, run_datetime, for_date), response)


async def get_cached_hfi_stats(run_type: str, run_datetime, for_date) -> Optional[HFIStatsResponse]:
    return await _get_cached(
        _run_key("hfi_stats", run_type, run_datetime, for_date), HFIStatsResponse
    )


async def put_cached_hfi_stats(run_type: str, run_datetime, for_date, response: HFIStatsResponse):
    await _put_cached(_run_key("hfi_stats", run_type, run_datetime, for_date), response)


async def get_cached_tpi_stats(run_type: str, run_datetime, for_date) -> Optional[TPIResponse]:
    return await _get_cached(_run_key("tpi_stats", run_type, run_datetime, for_date), TPIResponse)


async def put_cached_tpi_stats(run_type: str, run_datetime, for_date, response: TPIResponse):
    await _put_cached(_run_key("tpi_stats", run_type, run_datetime, for_date), response)
