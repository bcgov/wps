import os

from wps_shared.schemas.sfms import SFMSDailyActual
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


def create_mock_sfms_actuals():
    """Create mock SFMS daily actuals for testing."""
    return [
        SFMSDailyActual(
            code=100,
            lat=49.0,
            lon=-123.0,
            elevation=100.0,
            temperature=15.0,
            relative_humidity=50.0,
            precipitation=2.5,
            wind_speed=10.0,
            ffmc=85.0,
            dmc=30.0,
            dc=200.0,
        ),
        SFMSDailyActual(
            code=101,
            lat=49.5,
            lon=-123.5,
            elevation=200.0,
            temperature=12.0,
            relative_humidity=60.0,
            precipitation=5.0,
            wind_speed=8.0,
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
