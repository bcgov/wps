import os

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
    mock_wfwx_api,
)


def pytest_configure(config):
    """Set environment variables and configure ORIGINS before any imports happen."""
    os.environ.setdefault("ORIGINS", "testorigin")

    # Import main after setting env and patch ORIGINS to be a list for CORS middleware
    import app.main

    if isinstance(app.main.ORIGINS, str):
        app.main.ORIGINS = [app.main.ORIGINS]
