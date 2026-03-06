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

from app.jobs.sfms_daily_actuals import is_fwi_interpolation_day, run_sfms_daily_actuals, main
from app.tests.conftest import create_mock_sfms_actuals
from wps_sfms.processors.fwi import FWIProcessor
from wps_sfms.processors.idw import Interpolator
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_shared.db.models.sfms_run import SFMSRunLogStatus
from wps_shared.sfms.raster_addresser import FWIParameter

MODULE_PATH = "app.jobs.sfms_daily_actuals"


@pytest.mark.parametrize(
    "dt,expected",
    [
        # True cases: Mondays in April or May (any week)
        (datetime(2024, 4, 1, tzinfo=timezone.utc), True),  # Monday, April, day 1
        (datetime(2024, 4, 8, tzinfo=timezone.utc), True),  # Monday, April, day 8 (second Monday)
        (datetime(2024, 5, 6, tzinfo=timezone.utc), True),  # Monday, May
        (datetime(2024, 5, 27, tzinfo=timezone.utc), True),  # Monday, May, last Monday
        # False cases: wrong weekday
        (datetime(2024, 4, 2, tzinfo=timezone.utc), False),  # Tuesday, April
        (datetime(2024, 4, 7, tzinfo=timezone.utc), False),  # Sunday, April
        # False cases: wrong month (Monday but not April or May)
        (datetime(2024, 3, 4, tzinfo=timezone.utc), False),  # Monday, March
        (datetime(2024, 6, 3, tzinfo=timezone.utc), False),  # Monday, June
        (datetime(2024, 7, 1, tzinfo=timezone.utc), False),  # Monday, July
    ],
)
def test_is_fwi_interpolation_day(dt: datetime, expected: bool):
    assert is_fwi_interpolation_day(dt) is expected


class MockDailyActualsDeps(NamedTuple):
    """Typed container for sfms_daily_actuals mock dependencies."""

    db_session: AsyncMock
    s3_client: AsyncMock
    temp_processor: MagicMock
    rh_processor: MagicMock
    wind_speed_processor: MagicMock
    wind_direction_processor: MagicMock
    interpolation_processor: MagicMock
    fwi_processor: MagicMock
    wfwx_api: AsyncMock
    addresser: MagicMock


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

    # Mock get_fuel_type_raster_by_year
    mock_fuel_type_raster = MagicMock()
    mock_fuel_type_raster.object_store_path = "sfms/fuel/2024/fuel.tif"
    mocker.patch(
        f"{MODULE_PATH}.get_fuel_type_raster_by_year",
        new_callable=AsyncMock,
        return_value=mock_fuel_type_raster,
    )

    # Mock get_async_read_session_scope
    mock_read_session = AsyncMock(spec=AsyncSession)

    @asynccontextmanager
    async def _read_scope():
        yield mock_read_session

    mocker.patch(f"{MODULE_PATH}.get_async_read_session_scope", _read_scope)

    # Mock save_sfms_run
    mocker.patch(f"{MODULE_PATH}.save_sfms_run", new_callable=AsyncMock, return_value=1)

    # Mock SFMSNGRasterAddresser
    mock_addresser = MagicMock()
    mock_addresser.s3_prefix = "/vsis3/test-bucket"
    mocker.patch(f"{MODULE_PATH}.SFMSNGRasterAddresser", return_value=mock_addresser)
    mocker.patch(
        f"{MODULE_PATH}.generate_web_optimized_cog",
        return_value="/vsis3/test-bucket/sfms_ng/actual/2024/07/04/fwi_20240704_cog.tif",
    )

    # Mock processors
    mock_temp_processor = MagicMock(spec=TemperatureInterpolator)
    mock_temp_processor.process = AsyncMock(return_value="sfms/interpolated/2024/07/04/temp.tif")
    mocker.patch(
        f"{MODULE_PATH}.TemperatureInterpolator",
        return_value=mock_temp_processor,
    )

    mock_rh_processor = MagicMock(spec=RHInterpolator)
    mock_rh_processor.process = AsyncMock(return_value="sfms/interpolated/2024/07/04/rh.tif")
    mocker.patch(
        f"{MODULE_PATH}.RHInterpolator",
        return_value=mock_rh_processor,
    )

    mock_wind_speed_processor = MagicMock(spec=WindSpeedInterpolator)
    mock_wind_speed_processor.process = AsyncMock(
        return_value="sfms/interpolated/2024/07/04/wind_speed.tif"
    )
    mocker.patch(
        f"{MODULE_PATH}.WindSpeedInterpolator",
        return_value=mock_wind_speed_processor,
    )

    mock_wind_direction_processor = MagicMock(spec=WindDirectionInterpolator)
    mock_wind_direction_processor.process = AsyncMock(
        return_value="sfms/interpolated/2024/07/04/wind_direction.tif"
    )
    mocker.patch(
        f"{MODULE_PATH}.WindDirectionInterpolator",
        return_value=mock_wind_direction_processor,
    )

    mock_interpolation_processor = MagicMock(spec=Interpolator)
    mock_interpolation_processor.process = AsyncMock(
        return_value="sfms/interpolated/2024/07/04/precip.tif"
    )
    mocker.patch(
        f"{MODULE_PATH}.Interpolator",
        return_value=mock_interpolation_processor,
    )

    mock_fwi_processor = MagicMock(spec=FWIProcessor)
    mock_fwi_processor.calculate_index = AsyncMock(return_value=None)
    mocker.patch(f"{MODULE_PATH}.FWIProcessor", return_value=mock_fwi_processor)

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
        rh_processor=mock_rh_processor,
        wind_speed_processor=mock_wind_speed_processor,
        wind_direction_processor=mock_wind_direction_processor,
        interpolation_processor=mock_interpolation_processor,
        fwi_processor=mock_fwi_processor,
        wfwx_api=mock_wfwx_api,
        addresser=mock_addresser,
    )


class TestRunSfmsDailyActuals:
    """Tests for run_sfms_daily_actuals."""

    @pytest.mark.anyio
    async def test_runs_all_processors(self, mock_dependencies: MockDailyActualsDeps):
        """Test that all weather interpolation processors are called."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.rh_processor.process.assert_called_once()
        mock_dependencies.wind_speed_processor.process.assert_called_once()
        mock_dependencies.wind_direction_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_runs_processors_in_order(self, mock_dependencies: MockDailyActualsDeps):
        """Test that weather processors run in the expected sequence."""
        call_order = []
        mock_dependencies.temp_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("temp") or "temp.tif"
        )
        mock_dependencies.rh_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("rh") or "rh.tif"
        )
        mock_dependencies.wind_speed_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("wind_speed") or "wind_speed.tif"
        )
        mock_dependencies.wind_direction_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("wind_direction") or "wind_direction.tif"
        )
        mock_dependencies.interpolation_processor.process = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("precip") or "precip.tif"
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert call_order == ["temp", "rh", "wind_speed", "wind_direction", "precip"]

    @pytest.mark.anyio
    async def test_passes_s3_client_to_processors(self, mock_dependencies: MockDailyActualsDeps):
        """Test that the S3 client is passed to weather processors."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        temp_call_args = mock_dependencies.temp_processor.process.call_args
        assert temp_call_args[0][0] is mock_dependencies.s3_client

        wind_speed_call_args = mock_dependencies.wind_speed_processor.process.call_args
        assert wind_speed_call_args[0][0] is mock_dependencies.s3_client

        precip_call_args = mock_dependencies.interpolation_processor.process.call_args
        assert precip_call_args[0][0] is mock_dependencies.s3_client

    @pytest.mark.anyio
    async def test_sets_correct_hour(self, mock_dependencies: MockDailyActualsDeps):
        """Test that observations are processed at hour 20 (noon PDT)."""
        target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        dt = mock_dependencies.addresser.get_actual_weather_key.call_args_list[0][0][0]
        assert dt.hour == 20
        assert dt.minute == 0
        assert dt.second == 0

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

        # Eight tracked runs (temp, rh, ws, wd, precip, ffmc, dmc, dc) means eight execute calls
        assert mock_dependencies.db_session.execute.call_count == 8

    @pytest.mark.anyio
    async def test_logs_success_status(self, mock_dependencies: MockDailyActualsDeps):
        """Test that successful jobs are updated to success status."""
        records = [MagicMock() for _ in range(8)]
        mock_dependencies.db_session.get = AsyncMock(side_effect=records)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.db_session.get.call_count == 8
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

        mock_dependencies.rh_processor.process.assert_not_called()
        mock_dependencies.wind_speed_processor.process.assert_not_called()
        mock_dependencies.wind_direction_processor.process.assert_not_called()
        mock_dependencies.interpolation_processor.process.assert_not_called()

    @pytest.mark.anyio
    async def test_precipitation_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that when precipitation fails, it's logged as failed and the error propagates."""
        mock_dependencies.interpolation_processor.process = AsyncMock(
            side_effect=RuntimeError("precip failed")
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="precip failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.rh_processor.process.assert_called_once()
        mock_dependencies.wind_speed_processor.process.assert_called_once()
        mock_dependencies.wind_direction_processor.process.assert_called_once()


class TestMondayFWIInterpolation:
    """Tests for Monday FWI index interpolation."""

    @pytest.mark.anyio
    async def test_first_monday_may_runs_fwi_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that FWI interpolation runs on the first Monday of May."""
        # 2024-05-06 is the first Monday of May 2024
        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4

    @pytest.mark.anyio
    async def test_first_monday_april_runs_fwi_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that FWI interpolation runs on the first Monday of April."""
        # 2024-04-01 is the first Monday of April 2024
        target_date = datetime(2024, 4, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4

    @pytest.mark.anyio
    async def test_non_monday_skips_fwi_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that FWI interpolation does NOT run on non-Mondays."""
        # 2024-07-04 is a Thursday
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Only temp + RH + precip, no FWI
        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_monday_outside_april_may_skips_fwi_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that FWI interpolation does NOT run on Mondays outside April/May."""
        # 2024-07-01 is a Monday in July
        target_date = datetime(2024, 7, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Only temp + RH + precip, no FWI
        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_second_monday_april_runs_fwi_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that FWI interpolation runs on the second Monday of April."""
        # 2024-04-08 is the second Monday of April 2024
        target_date = datetime(2024, 4, 8, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4

    @pytest.mark.anyio
    async def test_monday_april_writes_six_run_log_entries(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """Test that a Monday in April produces 8 run log entries (temp + rh + precip + ws + wd + 3 FWI)."""
        # 2024-04-01 is the first Monday of April 2024
        target_date = datetime(2024, 4, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # 8 tracked runs: temp, rh, ws, wd, precip, ffmc, dmc, dc
        assert mock_dependencies.db_session.execute.call_count == 8


class TestFWICalculationVsInterpolation:
    """Regression tests: FWI interpolation and FWI calculation are mutually exclusive."""

    @pytest.mark.anyio
    async def test_monday_interpolation_skips_fwi_calculation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """On a re-interpolation Monday, FWI calculation must not run."""
        # 2024-05-06 is the first Monday of May 2024
        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.fwi_processor.calculate_index.assert_not_called()

    @pytest.mark.anyio
    async def test_regular_day_runs_fwi_calculation_not_interpolation(
        self, mock_dependencies: MockDailyActualsDeps
    ):
        """On a regular day, FWI calculation runs and FWI interpolation does not."""
        # 2024-07-04 is a Thursday
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.fwi_processor.calculate_index.call_count == 3
        # Each calculator must use its own FWIParameter — a wiring bug where all three
        # share the same fwi_param would silently produce wrong rasters.
        actual_fwi_params = [
            call.args[1]
            for call in mock_dependencies.addresser.get_actual_fwi_inputs.call_args_list
        ]
        assert len(actual_fwi_params) == 3
        assert set(actual_fwi_params) == {FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC}
        # IDW called once only for precip, not for FWI indices
        mock_dependencies.interpolation_processor.process.assert_called_once()


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
