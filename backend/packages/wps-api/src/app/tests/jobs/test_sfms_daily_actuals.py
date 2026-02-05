"""Unit tests for SFMS daily actuals job."""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.sfms_daily_actuals import run_sfms_daily_actuals, main
from app.tests.conftest import create_mock_sfms_actuals
from wps_shared.db.models.sfms_run_log import SFMSRunLogStatus

MODULE_PATH = "app.jobs.sfms_daily_actuals"


class MockDailyActualsDeps(NamedTuple):
    """Typed container for sfms_daily_actuals mock dependencies."""

    db_session: AsyncMock
    s3_client: AsyncMock
    temp_processor: MagicMock
    idw_processor: MagicMock
    wfwx_api: AsyncMock


@pytest.fixture
def mock_dependencies(mocker: MockerFixture, mock_s3_client, mock_wfwx_api) -> MockDailyActualsDeps:
    """Mock all external dependencies for run_sfms_daily_actuals."""
    # Mock S3Client
    mocker.patch(f"{MODULE_PATH}.S3Client", return_value=mock_s3_client)

    # Mock ClientSession
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(f"{MODULE_PATH}.ClientSession", return_value=mock_session)

    # Mock WfwxApi
    mock_wfwx_api.get_sfms_daily_actuals_all_stations = AsyncMock(
        return_value=create_mock_sfms_actuals()
    )
    mocker.patch(f"{MODULE_PATH}.WfwxApi", return_value=mock_wfwx_api)

    # Mock find_latest_version
    mocker.patch(
        f"{MODULE_PATH}.find_latest_version",
        new_callable=AsyncMock,
        return_value=1,
    )

    # Mock RasterKeyAddresser
    mock_addresser = MagicMock()
    mock_addresser.get_fuel_raster_key.return_value = "sfms/fuel/2024/fuel.tif"
    mock_addresser.s3_prefix = "/vsis3/test-bucket"
    mocker.patch(f"{MODULE_PATH}.RasterKeyAddresser", return_value=mock_addresser)

    # Mock processors
    mock_temp_processor = MagicMock()
    mock_temp_processor.process = AsyncMock(return_value="sfms/interpolated/2024/07/04/temp.tif")
    mocker.patch(
        f"{MODULE_PATH}.TemperatureInterpolationProcessor",
        return_value=mock_temp_processor,
    )

    mock_idw_processor = MagicMock()
    mock_idw_processor.process = AsyncMock(
        return_value="sfms/interpolated/2024/07/04/precip.tif"
    )
    mocker.patch(
        f"{MODULE_PATH}.IDWInterpolationProcessor",
        return_value=mock_idw_processor,
    )

    # Mock DB session
    db_session = AsyncMock(spec=AsyncSession)
    db_session.get = AsyncMock(return_value=MagicMock())

    @asynccontextmanager
    async def _scope():
        yield db_session

    mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope", _scope)

    return MockDailyActualsDeps(
        db_session=db_session,
        s3_client=mock_s3_client,
        temp_processor=mock_temp_processor,
        idw_processor=mock_idw_processor,
        wfwx_api=mock_wfwx_api,
    )


class TestRunSfmsDailyActuals:
    """Tests for run_sfms_daily_actuals."""

    @pytest.mark.anyio
    async def test_runs_both_processors(self, mock_dependencies: MockDailyActualsDeps):
        """Test that both temperature and precipitation processors are called."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.idw_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_runs_temperature_before_precipitation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that temperature interpolation runs before precipitation."""
        call_order = []
        mock_dependencies.temp_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("temp") or "temp.tif"
        )
        mock_dependencies.idw_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("precip") or "precip.tif"
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert call_order == ["temp", "precip"]

    @pytest.mark.anyio
    async def test_passes_s3_client_to_processors(self, mock_dependencies: MockDailyActualsDeps):
        """Test that the S3 client is passed to both processors."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        temp_call_args = mock_dependencies.temp_processor.process.call_args
        assert temp_call_args[0][0] is mock_dependencies.s3_client

        precip_call_args = mock_dependencies.idw_processor.process.call_args
        assert precip_call_args[0][0] is mock_dependencies.s3_client

    @pytest.mark.anyio
    async def test_sets_correct_hour(
        self, mock_dependencies: MockDailyActualsDeps, mocker: MockerFixture
    ):
        """Test that processors are initialized with hour 20 (noon PDT)."""
        captured_datetime = None

        def capture_temp_init(datetime_to_process, _raster_addresser):
            nonlocal captured_datetime
            captured_datetime = datetime_to_process
            return mock_dependencies.temp_processor

        mocker.patch(
            f"{MODULE_PATH}.TemperatureInterpolationProcessor",
            side_effect=capture_temp_init,
        )

        target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert captured_datetime is not None
        assert captured_datetime.hour == 20
        assert captured_datetime.minute == 0
        assert captured_datetime.second == 0

    @pytest.mark.anyio
    async def test_raises_on_empty_actuals(self, mock_dependencies: MockDailyActualsDeps):
        """Test that run raises RuntimeError when no station data is found."""
        mock_dependencies.wfwx_api.get_sfms_daily_actuals_all_stations = AsyncMock(return_value=[])

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No station observations found"):
            await run_sfms_daily_actuals(target_date)

    @pytest.mark.anyio
    async def test_writes_run_log_entries(self, mock_dependencies: MockDailyActualsDeps):
        """Test that run log records are added to the session."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Two tracked runs means two session.add calls
        assert mock_dependencies.db_session.add.call_count == 2

    @pytest.mark.anyio
    async def test_logs_success_status(self, mock_dependencies: MockDailyActualsDeps):
        """Test that successful jobs are updated to success status."""
        records = [MagicMock(), MagicMock()]
        mock_dependencies.db_session.get = AsyncMock(side_effect=records)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.db_session.get.call_count == 2
        for record in records:
            assert record.status == SFMSRunLogStatus.SUCCESS
            assert record.completed_at is not None

    @pytest.mark.anyio
    async def test_temperature_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that when temperature fails, it's logged as failed and the error propagates."""
        mock_dependencies.temp_processor.process = AsyncMock(
            side_effect=RuntimeError("temp failed")
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temp failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.idw_processor.process.assert_not_called()

    @pytest.mark.anyio
    async def test_precipitation_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that when precipitation fails, it's logged as failed and the error propagates."""
        mock_dependencies.idw_processor.process = AsyncMock(
            side_effect=RuntimeError("precip failed")
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="precip failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()


class TestMondayFWIInterpolation:
    """Tests for Monday FWI index interpolation."""

    @pytest.mark.anyio
    async def test_monday_runs_fwi_interpolation(self, mock_dependencies: MockDailyActualsDeps):
        """Test that FWI interpolation runs on Mondays (3 additional processor calls)."""
        # 2024-07-01 is a Monday
        target_date = datetime(2024, 7, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, precip processor called 4 times (1 precip + 3 FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.idw_processor.process.call_count == 4

    @pytest.mark.anyio
    async def test_non_monday_skips_fwi_interpolation(self, mock_dependencies: MockDailyActualsDeps):
        """Test that FWI interpolation does NOT run on non-Mondays."""
        # 2024-07-04 is a Thursday
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Only temp + precip, no FWI
        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.idw_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_monday_writes_five_run_log_entries(self, mock_dependencies: MockDailyActualsDeps):
        """Test that Monday produces 5 run log entries (temp + precip + 3 FWI)."""
        # 2024-07-01 is a Monday
        target_date = datetime(2024, 7, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # 5 tracked runs: temp, precip, ffmc, dmc, dc
        assert mock_dependencies.db_session.add.call_count == 5


class TestMain:
    """Tests for main() entry point."""

    def test_main_with_valid_date(self, mocker: MockerFixture):
        """Test main() parses a valid date argument."""
        mocker.patch.object(sys, "argv", ["sfms_daily_actuals.py", "2025-07-15"])
        mock_run = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_actuals", new_callable=AsyncMock)

        main()

        call_args = mock_run.call_args[0][0]
        assert call_args.year == 2025
        assert call_args.month == 7
        assert call_args.day == 15
        assert call_args.tzinfo == timezone.utc

    def test_main_without_date_uses_current(self, mocker: MockerFixture):
        """Test main() uses current UTC time when no date is provided."""
        mocker.patch.object(sys, "argv", ["sfms_daily_actuals.py"])
        mock_now = datetime(2025, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        mocker.patch(f"{MODULE_PATH}.get_utc_now", return_value=mock_now)
        mock_run = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_actuals", new_callable=AsyncMock)

        main()

        mock_run.assert_called_once_with(mock_now)

    def test_main_invalid_date_exits(self, mocker: MockerFixture):
        """Test main() exits with code 1 for an invalid date format."""
        mocker.patch.object(sys, "argv", ["sfms_daily_actuals.py", "not-a-date"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_job_exception_exits(self, mocker: MockerFixture):
        """Test main() exits with EX_SOFTWARE when the job raises."""
        mocker.patch.object(sys, "argv", ["sfms_daily_actuals.py", "2025-07-15"])
        mocker.patch(
            f"{MODULE_PATH}.run_sfms_daily_actuals",
            new_callable=AsyncMock,
            side_effect=RuntimeError("job failed"),
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == os.EX_SOFTWARE
