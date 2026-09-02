"""Unit tests for app.auto_spatial_advisory.advisory_run_stats.cache -- the Redis get/put
wrappers used by advisory_run_stats to avoid re-hitting Postgres for data that's immutable once
an SFMS run completes."""

from unittest.mock import MagicMock

import pytest
from wps_shared.schemas.fba import HFIStatsResponse, ProvincialSummaryResponse, TPIResponse

from app.auto_spatial_advisory.advisory_run_stats.cache import (
    create_redis as real_create_redis,
    get_cached_hfi_stats,
    get_cached_provincial_summary,
    get_cached_tpi_stats,
    put_cached_hfi_stats,
    put_cached_provincial_summary,
    put_cached_tpi_stats,
)

RUN_TYPE = "forecast"
RUN_DATETIME = "2024-07-15T12:00:00+00:00"
FOR_DATE = "2024-07-15"


@pytest.mark.anyio
async def test_get_cached_hfi_stats_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    result = await get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_then_get_cached_hfi_stats_round_trips(mocker):
    response = HFIStatsResponse(zone_data={})
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    await put_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_hfi_stats_redis_error_treated_as_miss(mocker):
    """A Redis connection error must not break the request -- fall back to the DB, same as a
    plain cache miss."""
    mock_redis = MagicMock()
    mock_redis.get.side_effect = ConnectionError("redis unavailable")
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    result = await get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_cached_hfi_stats_redis_error_does_not_raise(mocker):
    """A Redis error on write must not break the request -- the response was already fetched
    and is about to be returned regardless of whether caching it succeeds."""
    mock_redis = MagicMock()
    mock_redis.set.side_effect = ConnectionError("redis unavailable")
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    await put_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, HFIStatsResponse(zone_data={}))  # does not raise


@pytest.mark.anyio
async def test_put_then_get_cached_provincial_summary_round_trips(mocker):
    response = ProvincialSummaryResponse(provincial_summary=[])
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    await put_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_provincial_summary_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    result = await get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_then_get_cached_tpi_stats_round_trips(mocker):
    response = TPIResponse(firezone_tpi_stats=[])
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    await put_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_tpi_stats_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.create_redis", return_value=mock_redis)

    result = await get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


def test_create_redis_sets_connect_and_socket_timeouts(mocker):
    """A hung, unreachable Redis host must not block the event loop indefinitely -- confirm the
    client is actually built with bounded timeouts, not relying on redis-py's untimed default.

    Calls the real_create_redis reference captured at module import time (above), not the
    module attribute -- the autouse mock_advisory_run_stats_redis fixture (tests/conftest.py)
    replaces that attribute for every test so other tests don't hit a real Redis, which would
    make this test exercise the mock instead of the function it's meant to verify."""
    mock_strict_redis = mocker.patch("app.auto_spatial_advisory.advisory_run_stats.cache.StrictRedis")

    real_create_redis()

    _, kwargs = mock_strict_redis.call_args
    assert kwargs["socket_connect_timeout"] is not None
    assert kwargs["socket_timeout"] is not None
