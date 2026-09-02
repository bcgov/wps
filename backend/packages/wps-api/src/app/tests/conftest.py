import os
from datetime import datetime, timezone

import app.auto_spatial_advisory.advisory_run_stats.cache as advisory_run_stats_cache
import pytest
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.schemas.sfms import SFMSDaily
from wps_shared.tests.conftest import (
    anyio_backend,
    mock_env,
    mock_aiobotocore_get_session,
    mock_requests,
    mock_redis,
    mock_get_now,
    mock_get_pst_today_start_and_end,
    mock_session,
    mock_jwt_decode,
    mock_test_idir_jwt_decode,
    mock_sentry,
    mock_requests_session,
    mock_client_session,
    spy_access_logging,
    mock_s3_client,
    mock_wfwx_api,
)

SFMS_DAILY_FOR_DATETIME = datetime(2025, 7, 15, 20, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def mock_advisory_run_stats_redis(monkeypatch):
    """Same safe-by-default behaviour as wps_shared's mock_redis fixture, but for
    advisory_run_stats.cache's own Redis client. That client is built directly with an
    explicit connect/socket timeout rather than via wps_shared.utils.redis.create_redis (see
    cache.py), so it isn't covered by mock_redis patching _create_redis there -- without this,
    tests would hit a real Redis if one happens to be reachable, breaking isolation between
    test runs (a cache write in one test could produce a cache hit in a later one)."""

    class MockRedis:
        def get(self, name):
            return None

        def set(self, name, value, ex=None, px=None, nx=False, xx=False, keepttl=False):
            pass

        def delete(self, name):
            pass

    monkeypatch.setattr(advisory_run_stats_cache, "create_redis", lambda: MockRedis())


def create_mock_sfms_actuals():
    """Create mock SFMS daily actuals for testing."""
    return [
        SFMSDaily(
            code=100,
            for_datetime=SFMS_DAILY_FOR_DATETIME,
            run_type=RunTypeEnum.actual,
            lat=49.0,
            lon=-123.0,
            elevation=100.0,
            temperature=15.0,
            relative_humidity=50.0,
            precipitation=2.5,
            wind_speed=10.0,
            wind_direction=180.0,
            ffmc=85.0,
            dmc=30.0,
            dc=200.0,
        ),
        SFMSDaily(
            code=101,
            for_datetime=SFMS_DAILY_FOR_DATETIME,
            run_type=RunTypeEnum.actual,
            lat=49.5,
            lon=-123.5,
            elevation=200.0,
            temperature=12.0,
            relative_humidity=60.0,
            precipitation=5.0,
            wind_speed=8.0,
            wind_direction=200.0,
            ffmc=80.0,
            dmc=25.0,
            dc=180.0,
        ),
    ]


def pytest_configure(config):
    """Set environment variables and configure ORIGINS before any imports happen."""
    os.environ.setdefault("ORIGINS", "testorigin")

    # Import main after setting env and patch ORIGINS to be a list for CORS middleware
    import app.main

    if isinstance(app.main.ORIGINS, str):
        app.main.ORIGINS = [app.main.ORIGINS]
