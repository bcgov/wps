import os
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

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
)


class MockDependencies(NamedTuple):
    """Typed container for mock dependencies."""

    session: AsyncMock
    processor: MagicMock
    addresser: MagicMock


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
        ),
    ]


def create_interpolation_job_mocks(mocker, s3_client_mock, module_path: str, processor_class) -> MockDependencies:
    """
    Create common mock dependencies for interpolation job tests.

    :param mocker: pytest-mock fixture
    :param s3_client_mock: mock S3 client fixture
    :param module_path: module path prefix (e.g., "app.jobs.temperature_interpolation_job")
    :param processor_class: the processor class to mock (for spec)
    :return: MockDependencies named tuple
    """
    from aiohttp import ClientSession
    from wps_shared.sfms.raster_addresser import RasterKeyAddresser

    mocker.patch(f"{module_path}.S3Client", return_value=s3_client_mock)

    session_mock = AsyncMock(spec=ClientSession)
    session_mock.__aenter__ = AsyncMock(return_value=session_mock)
    session_mock.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(f"{module_path}.ClientSession", return_value=session_mock)

    mocker.patch(
        f"{module_path}.get_auth_header",
        return_value=AsyncMock(return_value={"Authorization": "Bearer test"})(),
    )
    mocker.patch(
        f"{module_path}.get_stations_from_source",
        return_value=AsyncMock(return_value=[])(),
    )
    mocker.patch(
        f"{module_path}.fetch_station_actuals",
        return_value=AsyncMock(return_value=create_mock_sfms_actuals())(),
    )
    mocker.patch(
        f"{module_path}.find_latest_version",
        return_value=AsyncMock(return_value=1)(),
    )

    mock_addresser = MagicMock(spec=RasterKeyAddresser)
    mock_addresser.get_fuel_raster_key.return_value = "sfms/fuel/2024/fuel.tif"
    mock_addresser.s3_prefix = "/vsis3/test-bucket"
    mock_addresser.get_mask_key.return_value = "/vsis3/test-bucket/sfms/static/bc_mask.tif"
    mock_addresser.get_dem_key.return_value = "/vsis3/test-bucket/sfms/static/bc_elevation.tif"
    mocker.patch(f"{module_path}.RasterKeyAddresser", return_value=mock_addresser)

    mock_processor = MagicMock(spec=processor_class)
    mock_processor.process = AsyncMock(return_value="sfms/interpolated/2024/07/04/output.tif")
    mocker.patch(f"{module_path}.{processor_class.__name__}", return_value=mock_processor)

    mocker.patch(f"{module_path}.send_rocketchat_notification", return_value=None)

    return MockDependencies(
        session=session_mock,
        processor=mock_processor,
        addresser=mock_addresser,
    )


def pytest_configure(config):
    """Set environment variables and configure ORIGINS before any imports happen."""
    os.environ.setdefault("ORIGINS", "testorigin")

    # Import main after setting env and patch ORIGINS to be a list for CORS middleware
    import app.main

    if isinstance(app.main.ORIGINS, str):
        app.main.ORIGINS = [app.main.ORIGINS]
