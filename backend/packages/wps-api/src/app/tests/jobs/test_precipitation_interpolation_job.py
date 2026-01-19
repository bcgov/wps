"""Unit tests for precipitation interpolation job."""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from aiohttp import ClientSession
from app.jobs.precipitation_interpolation_job import (
    PrecipitationInterpolationJob,
    main,
)
from app.tests.conftest import MockDependencies, create_mock_sfms_actuals
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_sfms.processors import PrecipitationInterpolationProcessor


@pytest.fixture
def mock_dependencies(mocker: MockerFixture, mock_s3_client):
    """Mock all external dependencies for the precipitation interpolation job."""
    # Use shared mock_s3_client fixture
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.S3Client",
        return_value=mock_s3_client,
    )

    # Mock ClientSession
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.ClientSession",
        return_value=mock_session,
    )

    # Mock auth header
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.get_auth_header",
        return_value=AsyncMock(return_value={"Authorization": "Bearer test"})(),
    )

    # Mock stations
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.get_stations_from_source",
        return_value=AsyncMock(return_value=[])(),
    )

    # Mock fetch_station_actuals
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.fetch_station_actuals",
        return_value=AsyncMock(return_value=create_mock_sfms_actuals())(),
    )

    # Mock find_latest_version
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.find_latest_version",
        return_value=AsyncMock(return_value=1)(),
    )

    # Mock RasterKeyAddresser
    mock_addresser = MagicMock(spec=RasterKeyAddresser)
    mock_addresser.get_fuel_raster_key.return_value = "sfms/fuel/2024/fuel.tif"
    mock_addresser.s3_prefix = "/vsis3/test-bucket"
    mock_addresser.get_mask_key.return_value = "/vsis3/test-bucket/sfms/static/bc_mask.tif"
    mock_addresser.get_interpolated_key.return_value = "sfms/interpolated/precip/2024/07/04/precip_20240704.tif"
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.RasterKeyAddresser",
        return_value=mock_addresser,
    )

    # Mock processor
    mock_processor = MagicMock(spec=PrecipitationInterpolationProcessor)
    mock_processor.process = AsyncMock(
        return_value="sfms/interpolated/precip/2024/07/04/precip_20240704.tif"
    )
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.PrecipitationInterpolationProcessor",
        return_value=mock_processor,
    )

    # Mock rocketchat
    mocker.patch(
        "app.jobs.precipitation_interpolation_job.send_rocketchat_notification",
        return_value=None,
    )

    return MockDependencies(
        session=mock_session,
        processor=mock_processor,
        addresser=mock_addresser,
    )


class TestPrecipitationInterpolationJob:
    """Tests for PrecipitationInterpolationJob class."""

    @pytest.mark.anyio
    async def test_run_success(self, mock_dependencies):
        """Test successful job run."""
        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await job.run(target_date)

        # Verify processor was called
        mock_dependencies.processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_run_creates_precipitation_data_source(self, mock_dependencies, mocker: MockerFixture):
        """Test that run() creates StationPrecipitationSource."""
        # Use mock_dependencies fixture for base mocking
        _ = mock_dependencies

        precip_source_mock = mocker.patch(
            "app.jobs.precipitation_interpolation_job.StationPrecipitationSource"
        )

        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await job.run(target_date)

        precip_source_mock.assert_called_once()

    @pytest.mark.anyio
    async def test_run_sets_correct_hour(self, mock_dependencies, mocker: MockerFixture):
        """Test that run() sets the hour to 20 (noon PDT)."""
        # Use mock_dependencies fixture for base mocking
        _ = mock_dependencies

        captured_datetime = None

        def capture_processor_init(datetime_to_process, _raster_addresser):
            nonlocal captured_datetime
            captured_datetime = datetime_to_process
            mock_proc = MagicMock()
            mock_proc.process = AsyncMock(return_value="test_key")
            return mock_proc

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.PrecipitationInterpolationProcessor",
            side_effect=capture_processor_init,
        )

        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)

        await job.run(target_date)

        assert captured_datetime is not None
        assert captured_datetime.hour == 20
        assert captured_datetime.minute == 0
        assert captured_datetime.second == 0

    @pytest.mark.anyio
    async def test_run_failure_sends_rocketchat(self, mocker: MockerFixture):
        """Test that failure sends rocketchat notification."""
        # Mock to raise an exception
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.S3Client",
            side_effect=Exception("S3 connection failed"),
        )

        rocketchat_spy = mocker.patch(
            "app.jobs.precipitation_interpolation_job.send_rocketchat_notification"
        )

        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(Exception, match="S3 connection failed"):
            await job.run(target_date)

        rocketchat_spy.assert_called_once()
        call_args = rocketchat_spy.call_args
        assert ":scream:" in call_args[0][0]
        assert "Interpolation job failed" in call_args[0][0]


class TestMain:
    """Tests for main() function."""

    def test_main_with_valid_date_argument(self, mock_dependencies, mocker: MockerFixture):
        """Test main() with a valid date argument."""
        # Use mock_dependencies fixture for base mocking
        _ = mock_dependencies

        mocker.patch.object(sys, "argv", ["precipitation_interpolation_job.py", "2024-07-04"])

        job_run_spy = mocker.patch.object(
            PrecipitationInterpolationJob,
            "run",
            new_callable=AsyncMock,
        )

        main()

        job_run_spy.assert_called_once()
        call_args = job_run_spy.call_args[0][0]
        assert call_args.year == 2024
        assert call_args.month == 7
        assert call_args.day == 4

    def test_main_without_date_uses_current(self, mock_dependencies, mocker: MockerFixture):
        """Test main() without date argument uses current date."""
        # Use mock_dependencies fixture for base mocking
        _ = mock_dependencies

        mocker.patch.object(sys, "argv", ["precipitation_interpolation_job.py"])

        mock_now = datetime(2024, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.get_utc_now",
            return_value=mock_now,
        )

        job_run_spy = mocker.patch.object(
            PrecipitationInterpolationJob,
            "run",
            new_callable=AsyncMock,
        )

        main()

        job_run_spy.assert_called_once()
        call_args = job_run_spy.call_args[0][0]
        assert call_args == mock_now

    def test_main_invalid_date_format_exits(self, mocker: MockerFixture):
        """Test main() exits with code 1 for invalid date format."""
        mocker.patch.object(sys, "argv", ["precipitation_interpolation_job.py", "invalid-date"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_exception_exits_with_software_error(self, mocker: MockerFixture):
        """Test main() exits with EX_SOFTWARE on exception."""
        mocker.patch.object(sys, "argv", ["precipitation_interpolation_job.py", "2024-07-04"])

        mocker.patch.object(
            PrecipitationInterpolationJob,
            "run",
            new_callable=AsyncMock,
            side_effect=Exception("Job failed"),
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == os.EX_SOFTWARE


class TestPrecipitationInterpolationJobIntegration:
    """Integration-style tests with more realistic mocking."""

    @pytest.mark.anyio
    async def test_processes_multiple_data_sources(self, mocker: MockerFixture, mock_s3_client):
        """Test that job processes all data sources in the list."""
        # Track how many times processor.process is called
        process_call_count = 0

        async def mock_process(*_args, **_kwargs):
            nonlocal process_call_count
            process_call_count += 1
            return f"output_key_{process_call_count}"

        mock_processor = MagicMock()
        mock_processor.process = mock_process

        # Use shared mock_s3_client fixture
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.S3Client",
            return_value=mock_s3_client,
        )

        # Mock ClientSession
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.ClientSession",
            return_value=mock_session,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.get_auth_header",
            new_callable=AsyncMock,
            return_value={},
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.get_stations_from_source",
            new_callable=AsyncMock,
            return_value=[],
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.fetch_station_actuals",
            new_callable=AsyncMock,
            return_value=create_mock_sfms_actuals(),
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.find_latest_version",
            new_callable=AsyncMock,
            return_value=1,
        )

        mock_addresser = MagicMock()
        mock_addresser.get_fuel_raster_key.return_value = "fuel.tif"
        mock_addresser.s3_prefix = "/vsis3/bucket"
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.RasterKeyAddresser",
            return_value=mock_addresser,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.PrecipitationInterpolationProcessor",
            return_value=mock_processor,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.send_rocketchat_notification"
        )

        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await job.run(target_date)

        # Job has one data source (StationPrecipitationSource), so process should be called once
        assert process_call_count == 1

    @pytest.mark.anyio
    async def test_uses_correct_fuel_raster_path(self, mocker: MockerFixture, mock_s3_client):
        """Test that the correct fuel raster path is constructed."""
        captured_fuel_path = None

        async def capture_process(_s3_client, fuel_path, _actuals, _source):
            nonlocal captured_fuel_path
            captured_fuel_path = fuel_path
            return "output_key"

        mock_processor = MagicMock()
        mock_processor.process = capture_process

        # Use shared mock_s3_client fixture
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.S3Client",
            return_value=mock_s3_client,
        )

        # Mock ClientSession
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.ClientSession",
            return_value=mock_session,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.get_auth_header",
            new_callable=AsyncMock,
            return_value={},
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.get_stations_from_source",
            new_callable=AsyncMock,
            return_value=[],
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.fetch_station_actuals",
            new_callable=AsyncMock,
            return_value=create_mock_sfms_actuals(),
        )
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.find_latest_version",
            new_callable=AsyncMock,
            return_value=2,
        )

        mock_addresser = MagicMock()
        mock_addresser.get_fuel_raster_key.return_value = "sfms/fuel/2024/07/04/fuel_v2.tif"
        mock_addresser.s3_prefix = "/vsis3/test-bucket"
        mocker.patch(
            "app.jobs.precipitation_interpolation_job.RasterKeyAddresser",
            return_value=mock_addresser,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.PrecipitationInterpolationProcessor",
            return_value=mock_processor,
        )

        mocker.patch(
            "app.jobs.precipitation_interpolation_job.send_rocketchat_notification"
        )

        job = PrecipitationInterpolationJob()
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await job.run(target_date)

        assert captured_fuel_path == "/vsis3/test-bucket/sfms/fuel/2024/07/04/fuel_v2.tif"
        mock_addresser.get_fuel_raster_key.assert_called_with(target_date, version=2)
