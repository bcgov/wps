"""Unit tests for app.auto_spatial_advisory.advisory_run_stats.cache -- the Redis-backed
ASARedisCache used by advisory_run_stats to avoid re-hitting Postgres for data that's immutable
once an SFMS run completes."""

from unittest.mock import MagicMock

import pytest
from wps_shared.schemas.fba import HFIStatsResponse, ProvincialSummaryResponse, TPIResponse

from app.auto_spatial_advisory.advisory_run_stats.cache import ASARedisCache, asa_stats_cache

RUN_TYPE = "forecast"
RUN_DATETIME = "2024-07-15T12:00:00+00:00"
FOR_DATE = "2024-07-15"


@pytest.mark.anyio
async def test_get_cached_hfi_stats_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    result = await asa_stats_cache.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_then_get_cached_hfi_stats_round_trips(mocker):
    response = HFIStatsResponse(zone_data={})
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    await asa_stats_cache.put_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await asa_stats_cache.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_hfi_stats_redis_error_treated_as_miss(mocker):
    """A Redis connection error must not break the request -- fall back to the DB, same as a
    plain cache miss."""
    mock_redis = MagicMock()
    mock_redis.get.side_effect = ConnectionError("redis unavailable")
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    result = await asa_stats_cache.get_cached_hfi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_cached_hfi_stats_redis_error_does_not_raise(mocker):
    """A Redis error on write must not break the request -- the response was already fetched
    and is about to be returned regardless of whether caching it succeeds."""
    mock_redis = MagicMock()
    mock_redis.set.side_effect = ConnectionError("redis unavailable")
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    await asa_stats_cache.put_cached_hfi_stats(
        RUN_TYPE, RUN_DATETIME, FOR_DATE, HFIStatsResponse(zone_data={})
    )  # does not raise


@pytest.mark.anyio
async def test_put_then_get_cached_provincial_summary_round_trips(mocker):
    response = ProvincialSummaryResponse(provincial_summary=[])
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    await asa_stats_cache.put_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await asa_stats_cache.get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_provincial_summary_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    result = await asa_stats_cache.get_cached_provincial_summary(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


@pytest.mark.anyio
async def test_put_then_get_cached_tpi_stats_round_trips(mocker):
    response = TPIResponse(firezone_tpi_stats=[])
    stored = {}

    mock_redis = MagicMock()
    mock_redis.set.side_effect = lambda key, value, ex=None: stored.__setitem__(key, value)
    mock_redis.get.side_effect = lambda key: stored.get(key)
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    await asa_stats_cache.put_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE, response)
    result = await asa_stats_cache.get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result == response


@pytest.mark.anyio
async def test_get_cached_tpi_stats_miss_returns_none(mocker):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mocker.patch.object(asa_stats_cache, "client", return_value=mock_redis)

    result = await asa_stats_cache.get_cached_tpi_stats(RUN_TYPE, RUN_DATETIME, FOR_DATE)

    assert result is None


def test_connection_kwargs_sets_connect_and_socket_timeouts():
    """A hung, unreachable Redis host must not block the event loop indefinitely -- confirm the
    connection config sets bounded timeouts, not relying on redis-py's untimed default.

    Exercises a fresh ASARedisCache(), not the module-level `asa_stats_cache` singleton --
    unaffected by the autouse mock_advisory_run_stats_redis fixture (tests/conftest.py), which
    only patches client() on that singleton instance, not the class. No mocking needed here."""
    kwargs = ASARedisCache().connection_kwargs()

    assert kwargs["socket_connect_timeout"] is not None
    assert kwargs["socket_timeout"] is not None


def test_client_builds_from_connection_kwargs():
    """client() is a StrictRedis(**connection_kwargs()) pass-through -- confirmed by inspecting
    the real, unconnected client's own connection_kwargs (StrictRedis doesn't eagerly connect
    on construction, so this doesn't touch a real Redis).

    Same fresh-instance reasoning as above -- a new ASARedisCache() here is a different object
    than the singleton the autouse fixture patches, so this exercises the real client()."""
    redis_cache = ASARedisCache()

    client = redis_cache.client()

    connection_kwargs = client.connection_pool.connection_kwargs
    expected = redis_cache.connection_kwargs()
    assert connection_kwargs["socket_connect_timeout"] == expected["socket_connect_timeout"]
    assert connection_kwargs["socket_timeout"] == expected["socket_timeout"]
    assert connection_kwargs["host"] == expected["host"]
    assert connection_kwargs["port"] == expected["port"]


def test_client_is_built_once_and_reused():
    """client() shouldn't pay a fresh TCP handshake on every call -- confirm repeated calls
    return the exact same StrictRedis instance rather than constructing a new one each time."""
    redis_cache = ASARedisCache()

    first = redis_cache.client()
    second = redis_cache.client()

    assert first is second
