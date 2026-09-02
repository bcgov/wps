"""Redis cache wrappers for advisory run stats (provincial summary, hfi-stats, tpi-stats, and
their fire-centre-scoped counterparts).

Safe to cache: this data is immutable once an SFMS run completes -- keyed on the run itself
(run_type/run_datetime/for_date, plus fire_centre_name for the scoped variants), so a new run
gets a new key rather than needing invalidation.
"""

import logging
from typing import Optional, TypeVar

from pydantic import TypeAdapter
from redis import StrictRedis
from wps_shared import config
from wps_shared.schemas.fba import (
    FireCentreTPIResponse,
    FireZoneHFIStats,
    HFIStatsResponse,
    ProvincialSummaryResponse,
    TPIResponse,
)

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


T = TypeVar("T")

# TypeAdapter (not just BaseModel) so the fire-centre-hfi-stats endpoint's plain
# dict[int, FireZoneHFIStats] response can be cached the same way as the BaseModel-shaped ones,
# without wrapping it in a schema it doesn't otherwise need.
_PROVINCIAL_SUMMARY_ADAPTER = TypeAdapter(ProvincialSummaryResponse)
_HFI_STATS_ADAPTER = TypeAdapter(HFIStatsResponse)
_TPI_STATS_ADAPTER = TypeAdapter(TPIResponse)
_FIRE_CENTRE_HFI_STATS_ADAPTER = TypeAdapter(dict[int, FireZoneHFIStats])
_FIRE_CENTRE_TPI_STATS_ADAPTER = TypeAdapter(FireCentreTPIResponse)


def _run_key(prefix: str, run_type: str, run_datetime, for_date) -> str:
    return f"{prefix}_{run_type}_{run_datetime}_{for_date}"


def _fire_centre_run_key(
    prefix: str, fire_centre_name: str, run_type: str, run_datetime, for_date
) -> str:
    return f"{prefix}_{fire_centre_name}_{run_type}_{run_datetime}_{for_date}"


async def _get_cached(key: str, adapter: TypeAdapter) -> Optional[T]:
    cache = create_redis()
    try:
        cached_json = cache.get(key)
    except Exception as error:
        cached_json = None
        logger.error(error, exc_info=error)
    if cached_json:
        logger.info("redis cache hit %s", key)
        return adapter.validate_json(cached_json)
    logger.info("redis cache miss %s", key)
    return None


async def _put_cached(key: str, value: T, adapter: TypeAdapter):
    cache = create_redis()
    try:
        cache.set(key, adapter.dump_json(value), ex=cache_expiry_seconds)
    except Exception as error:
        logger.error(error, exc_info=error)


async def get_cached_provincial_summary(
    run_type: str, run_datetime, for_date
) -> Optional[ProvincialSummaryResponse]:
    return await _get_cached(
        _run_key("provincial_summary", run_type, run_datetime, for_date),
        _PROVINCIAL_SUMMARY_ADAPTER,
    )


async def put_cached_provincial_summary(
    run_type: str, run_datetime, for_date, response: ProvincialSummaryResponse
):
    await _put_cached(
        _run_key("provincial_summary", run_type, run_datetime, for_date),
        response,
        _PROVINCIAL_SUMMARY_ADAPTER,
    )


async def get_cached_hfi_stats(run_type: str, run_datetime, for_date) -> Optional[HFIStatsResponse]:
    return await _get_cached(
        _run_key("hfi_stats", run_type, run_datetime, for_date), _HFI_STATS_ADAPTER
    )


async def put_cached_hfi_stats(run_type: str, run_datetime, for_date, response: HFIStatsResponse):
    await _put_cached(
        _run_key("hfi_stats", run_type, run_datetime, for_date), response, _HFI_STATS_ADAPTER
    )


async def get_cached_tpi_stats(run_type: str, run_datetime, for_date) -> Optional[TPIResponse]:
    return await _get_cached(
        _run_key("tpi_stats", run_type, run_datetime, for_date), _TPI_STATS_ADAPTER
    )


async def put_cached_tpi_stats(run_type: str, run_datetime, for_date, response: TPIResponse):
    await _put_cached(
        _run_key("tpi_stats", run_type, run_datetime, for_date), response, _TPI_STATS_ADAPTER
    )


async def get_cached_fire_centre_hfi_stats(
    fire_centre_name: str, run_type: str, run_datetime, for_date
) -> Optional[dict[int, FireZoneHFIStats]]:
    return await _get_cached(
        _fire_centre_run_key(
            "fire_centre_hfi_stats", fire_centre_name, run_type, run_datetime, for_date
        ),
        _FIRE_CENTRE_HFI_STATS_ADAPTER,
    )


async def put_cached_fire_centre_hfi_stats(
    fire_centre_name: str, run_type: str, run_datetime, for_date, value: dict[int, FireZoneHFIStats]
):
    await _put_cached(
        _fire_centre_run_key(
            "fire_centre_hfi_stats", fire_centre_name, run_type, run_datetime, for_date
        ),
        value,
        _FIRE_CENTRE_HFI_STATS_ADAPTER,
    )


async def get_cached_fire_centre_tpi_stats(
    fire_centre_name: str, run_type: str, run_datetime, for_date
) -> Optional[FireCentreTPIResponse]:
    return await _get_cached(
        _fire_centre_run_key(
            "fire_centre_tpi_stats", fire_centre_name, run_type, run_datetime, for_date
        ),
        _FIRE_CENTRE_TPI_STATS_ADAPTER,
    )


async def put_cached_fire_centre_tpi_stats(
    fire_centre_name: str, run_type: str, run_datetime, for_date, response: FireCentreTPIResponse
):
    await _put_cached(
        _fire_centre_run_key(
            "fire_centre_tpi_stats", fire_centre_name, run_type, run_datetime, for_date
        ),
        response,
        _FIRE_CENTRE_TPI_STATS_ADAPTER,
    )
