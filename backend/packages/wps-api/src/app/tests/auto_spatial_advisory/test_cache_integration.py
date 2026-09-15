"""Integration tests for advisory_run_stats.cache against a real Redis server.

These tests require Docker/Podman. Run with:
    cd backend && uv run pytest packages/wps-api/src/app/tests/auto_spatial_advisory/test_cache_integration.py

Mock-based tests (test_cache.py) exercise the same logic against a MagicMock -- they can't
catch a bug in how redis-py itself behaves. This file is why one was found: mocks never showed
that socket_connect_timeout doesn't cover DNS resolution, only a real unreachable Redis did
(see the timeout test below, and the asyncio.wait_for fix in cache.py).
"""

import time

import pytest
from testcontainers.redis import RedisContainer
from wps_shared.schemas.fba import (
    FireCentreTPIResponse,
    FireZoneHFIStats,
    HFIStatsResponse,
    ProvincialSummaryResponse,
    TPIResponse,
)

from app.auto_spatial_advisory.advisory_run_stats.cache import ASARedisCache

TESTCONTAINERS_REDIS_IMAGE = "redis:6-alpine"  # matches openshift/templates/redis.yaml's redis:6-el9

RUN_TYPE = "forecast"
RUN_DATETIME = "2025-01-01T12:00:00+00:00"
FOR_DATE = "2025-01-01"
FIRE_CENTRE_NAME = "Kamloops Fire Centre"

SAMPLE_ZONE_DATA = {1: FireZoneHFIStats(min_wind_stats=[], fuel_area_stats=[])}


@pytest.fixture
def redis_container():
    with RedisContainer(TESTCONTAINERS_REDIS_IMAGE) as container:
        yield container


@pytest.fixture
def real_cache(redis_container, monkeypatch):
    """A fresh ASARedisCache pointed at the real testcontainers Redis via the same
    REDIS_HOST/REDIS_PORT config path production uses -- not a mock, and not the module-level
    asa_stats_cache singleton (tests/conftest.py's autouse fixture keeps that one mocked)."""
    monkeypatch.setenv("REDIS_HOST", redis_container.get_container_host_ip())
    monkeypatch.setenv("REDIS_PORT", str(redis_container.get_exposed_port(6379)))
    return ASARedisCache()


@pytest.mark.anyio
async def test_put_then_get_round_trips_through_real_redis(real_cache):
    """Every put_cached_*/get_cached_* pair, called directly against a real Redis."""
    provincial_summary = ProvincialSummaryResponse(provincial_summary=[])
    await real_cache.put_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE, provincial_summary)
    assert await real_cache.get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE) == provincial_summary

    hfi_stats = HFIStatsResponse(zone_data=SAMPLE_ZONE_DATA)
    await real_cache.put_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, hfi_stats)
    assert await real_cache.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE) == hfi_stats

    tpi_stats = TPIResponse(firezone_tpi_stats=[])
    await real_cache.put_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, tpi_stats)
    assert await real_cache.get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE) == tpi_stats

    await real_cache.put_cached_fire_centre_hfi_stats(
        FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE, SAMPLE_ZONE_DATA
    )
    assert (
        await real_cache.get_cached_fire_centre_hfi_stats(FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE)
        == SAMPLE_ZONE_DATA
    )

    fire_centre_tpi_stats = FireCentreTPIResponse(fire_centre_name=FIRE_CENTRE_NAME, firezone_tpi_stats=[])
    await real_cache.put_cached_fire_centre_tpi_stats(
        FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE, fire_centre_tpi_stats
    )
    assert (
        await real_cache.get_cached_fire_centre_tpi_stats(FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE)
        == fire_centre_tpi_stats
    )


@pytest.mark.anyio
async def test_get_miss_returns_none_against_real_redis(real_cache):
    """Every get_cached_* on an empty key, called directly against a real Redis."""
    assert await real_cache.get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE) is None
    assert await real_cache.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE) is None
    assert await real_cache.get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE) is None
    assert (
        await real_cache.get_cached_fire_centre_hfi_stats(FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE)
        is None
    )
    assert (
        await real_cache.get_cached_fire_centre_tpi_stats(FIRE_CENTRE_NAME, RUN_TYPE, RUN_DATETIME, FOR_DATE)
        is None
    )


@pytest.mark.anyio
async def test_ttl_is_set_on_write(real_cache):
    response = ProvincialSummaryResponse(provincial_summary=[])

    await real_cache.put_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)

    key = f"provincial_summary_{RUN_TYPE}_{RUN_DATETIME}_{FOR_DATE}"
    ttl = real_cache.client().ttl(key)
    assert 0 < ttl <= 86400


@pytest.mark.anyio
async def test_unreachable_redis_falls_back_within_timeout(monkeypatch):
    """The actual bug found and fixed during manual pre-deploy testing: DNS resolution isn't
    covered by socket_connect_timeout, so an unreachable host used to take several seconds to
    fail instead of the configured timeout. No container needed -- port 1 refuses immediately
    at the OS level, isolating exactly the gap asyncio.wait_for was added to close."""
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_PORT", "1")
    unreachable = ASARedisCache(timeout_seconds=0.2)

    start = time.monotonic()
    result = await unreachable.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)
    elapsed = time.monotonic() - start

    assert result is None
    assert elapsed < 1.0
