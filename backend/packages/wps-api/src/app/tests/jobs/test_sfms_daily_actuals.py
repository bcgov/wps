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
from app.jobs.temperature_interpolation_job import TemperatureInterpolationJob
from app.jobs.precipitation_interpolation_job import PrecipitationInterpolationJob

MODULE_PATH = "app.jobs.sfms_daily_actuals"


class MockDailyActualsDeps(NamedTuple):
    """Typed container for sfms_daily_actuals mock dependencies."""

    session: AsyncMock
    temp_job: MagicMock
    precip_job: MagicMock


@pytest.fixture
def mock_dependencies(mocker: MockerFixture) -> MockDailyActualsDeps:
    """Mock all external dependencies for run_sfms_daily_actuals."""
    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=MagicMock())

    @asynccontextmanager
    async def _scope():
        yield session

    mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope", _scope)

    temp_job = MagicMock(spec=TemperatureInterpolationJob)
    temp_job.run = AsyncMock()
    mocker.patch(f"{MODULE_PATH}.TemperatureInterpolationJob", return_value=temp_job)

    precip_job = MagicMock(spec=PrecipitationInterpolationJob)
    precip_job.run = AsyncMock()
    mocker.patch(f"{MODULE_PATH}.PrecipitationInterpolationJob", return_value=precip_job)

    return MockDailyActualsDeps(session=session, temp_job=temp_job, precip_job=precip_job)


class TestRunSfmsDailyActuals:
    """Tests for run_sfms_daily_actuals."""

    @pytest.mark.anyio
    async def test_runs_both_interpolation_jobs(self, mock_dependencies: MockDailyActualsDeps):
        """Test that both temperature and precipitation jobs are run."""
        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_job.run.assert_called_once_with(target_date)
        mock_dependencies.precip_job.run.assert_called_once_with(target_date)

    @pytest.mark.anyio
    async def test_runs_temperature_before_precipitation(self, mock_dependencies: MockDailyActualsDeps):
        """Test that temperature interpolation runs before precipitation."""
        call_order = []
        mock_dependencies.temp_job.run = AsyncMock(side_effect=lambda _: call_order.append("temp"))
        mock_dependencies.precip_job.run = AsyncMock(side_effect=lambda _: call_order.append("precip"))

        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert call_order == ["temp", "precip"]

    @pytest.mark.anyio
    async def test_writes_run_log_entries(self, mock_dependencies: MockDailyActualsDeps):
        """Test that run log records are added to the session."""
        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Two jobs means two session.add calls (one per tracked job)
        assert mock_dependencies.session.add.call_count == 2

    @pytest.mark.anyio
    async def test_logs_success_status(self, mock_dependencies: MockDailyActualsDeps):
        """Test that successful jobs are updated to success status."""
        records = [MagicMock(), MagicMock()]
        mock_dependencies.session.get = AsyncMock(side_effect=records)

        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.session.get.call_count == 2
        for record in records:
            assert record.status == "success"
            assert record.completed_at is not None

    @pytest.mark.anyio
    async def test_temperature_failure_logs_failed_and_raises(self, mock_dependencies: MockDailyActualsDeps):
        """Test that when temperature fails, it's logged as failed and the error propagates."""
        mock_dependencies.temp_job.run = AsyncMock(side_effect=RuntimeError("temp failed"))

        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temp failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.precip_job.run.assert_not_called()

    @pytest.mark.anyio
    async def test_precipitation_failure_logs_failed_and_raises(self, mock_dependencies: MockDailyActualsDeps):
        """Test that when precipitation fails, it's logged as failed and the error propagates."""
        mock_dependencies.precip_job.run = AsyncMock(side_effect=RuntimeError("precip failed"))

        target_date = datetime(2025, 7, 15, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="precip failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_job.run.assert_called_once()


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
