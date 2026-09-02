"""Redis cache for advisory run stats (provincial summary, hfi-stats, tpi-stats, and their
fire-centre-scoped counterparts).

Safe to cache: this data is immutable once an SFMS run completes because it's keyed on the run itself
(run_type/run_datetime/for_date, plus fire_centre_name for the scoped variants), so a new run
gets a new key rather than needing invalidation.
"""

import asyncio
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


class ASARedisCache:
    """Wraps the Redis connection as an object, not module-level state: a fresh ASARedisCache()
    exercises connection_kwargs()/client() in isolation, while the `asa_stats_cache` singleton
    below is the one thing tests mock (see tests/conftest.py's autouse
    mock_advisory_run_stats_redis)."""

    def __init__(self, timeout_seconds: float = 1):
        # socket_connect_timeout/socket_timeout below don't cover DNS resolution (getaddrinfo)
        # _get()/_put() wrap the whole call in asyncio.wait_for(timeout_seconds) as the real ceiling,
        # via asyncio.to_thread so this blocking redis-py call doesn't sit on the event loop.
        self._timeout_seconds = timeout_seconds
        self._client: Optional[StrictRedis] = None

    def connection_kwargs(self) -> dict:
        return {
            "host": config.get("REDIS_HOST"),
            "port": config.get("REDIS_PORT", 6379),
            "db": 0,
            "password": config.get("REDIS_PASSWORD"),
            "socket_connect_timeout": self._timeout_seconds,
            "socket_timeout": self._timeout_seconds,
        }

    def client(self) -> StrictRedis:
        # Built once and reused, not per call -- redis-py's own connection pool is already
        # safe for repeated/concurrent use, so rebuilding here would pay a fresh TCP handshake
        # on every single cache get/put instead of reusing one open connection.
        if self._client is None:
            self._client = StrictRedis(**self.connection_kwargs())
        return self._client

    async def _get(self, key: str, adapter: TypeAdapter) -> Optional[T]:
        try:
            cached_json = await asyncio.wait_for(
                asyncio.to_thread(self.client().get, key), timeout=self._timeout_seconds
            )
        except Exception as error:
            cached_json = None
            logger.error(error, exc_info=error)
        if cached_json:
            logger.info("redis cache hit %s", key)
            return adapter.validate_json(cached_json)
        logger.info("redis cache miss %s", key)
        return None

    async def _put(self, key: str, value: T, adapter: TypeAdapter):
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    self.client().set, key, adapter.dump_json(value), ex=cache_expiry_seconds
                ),
                timeout=self._timeout_seconds,
            )
        except Exception as error:
            logger.error(error, exc_info=error)

    async def get_cached_provincial_summary(
        self, run_type: str, run_datetime, for_date
    ) -> Optional[ProvincialSummaryResponse]:
        return await self._get(
            _run_key("provincial_summary", run_type, run_datetime, for_date),
            _PROVINCIAL_SUMMARY_ADAPTER,
        )

    async def put_cached_provincial_summary(
        self, run_type: str, run_datetime, for_date, response: ProvincialSummaryResponse
    ):
        await self._put(
            _run_key("provincial_summary", run_type, run_datetime, for_date),
            response,
            _PROVINCIAL_SUMMARY_ADAPTER,
        )

    async def get_cached_hfi_stats(
        self, run_type: str, run_datetime, for_date
    ) -> Optional[HFIStatsResponse]:
        return await self._get(
            _run_key("hfi_stats", run_type, run_datetime, for_date), _HFI_STATS_ADAPTER
        )

    async def put_cached_hfi_stats(
        self, run_type: str, run_datetime, for_date, response: HFIStatsResponse
    ):
        await self._put(
            _run_key("hfi_stats", run_type, run_datetime, for_date), response, _HFI_STATS_ADAPTER
        )

    async def get_cached_tpi_stats(
        self, run_type: str, run_datetime, for_date
    ) -> Optional[TPIResponse]:
        return await self._get(
            _run_key("tpi_stats", run_type, run_datetime, for_date), _TPI_STATS_ADAPTER
        )

    async def put_cached_tpi_stats(
        self, run_type: str, run_datetime, for_date, response: TPIResponse
    ):
        await self._put(
            _run_key("tpi_stats", run_type, run_datetime, for_date), response, _TPI_STATS_ADAPTER
        )

    async def get_cached_fire_centre_hfi_stats(
        self, fire_centre_name: str, run_type: str, run_datetime, for_date
    ) -> Optional[dict[int, FireZoneHFIStats]]:
        return await self._get(
            _fire_centre_run_key(
                "fire_centre_hfi_stats", fire_centre_name, run_type, run_datetime, for_date
            ),
            _FIRE_CENTRE_HFI_STATS_ADAPTER,
        )

    async def put_cached_fire_centre_hfi_stats(
        self,
        fire_centre_name: str,
        run_type: str,
        run_datetime,
        for_date,
        value: dict[int, FireZoneHFIStats],
    ):
        await self._put(
            _fire_centre_run_key(
                "fire_centre_hfi_stats", fire_centre_name, run_type, run_datetime, for_date
            ),
            value,
            _FIRE_CENTRE_HFI_STATS_ADAPTER,
        )

    async def get_cached_fire_centre_tpi_stats(
        self, fire_centre_name: str, run_type: str, run_datetime, for_date
    ) -> Optional[FireCentreTPIResponse]:
        return await self._get(
            _fire_centre_run_key(
                "fire_centre_tpi_stats", fire_centre_name, run_type, run_datetime, for_date
            ),
            _FIRE_CENTRE_TPI_STATS_ADAPTER,
        )

    async def put_cached_fire_centre_tpi_stats(
        self,
        fire_centre_name: str,
        run_type: str,
        run_datetime,
        for_date,
        response: FireCentreTPIResponse,
    ):
        await self._put(
            _fire_centre_run_key(
                "fire_centre_tpi_stats", fire_centre_name, run_type, run_datetime, for_date
            ),
            response,
            _FIRE_CENTRE_TPI_STATS_ADAPTER,
        )


asa_stats_cache = ASARedisCache()
