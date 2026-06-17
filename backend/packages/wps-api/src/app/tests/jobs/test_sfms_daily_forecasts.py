"""Unit tests for SFMS daily forecasts job."""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from wps_sfms.processors.fwi import FWIProcessor
from wps_sfms.processors.idw import Interpolator
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter

from app.jobs.sfms_daily_forecasts import forecast_datetimes, main, run_sfms_daily_forecasts
from app.tests.conftest import create_mock_sfms_actuals

MODULE_PATH = "app.jobs.sfms_daily_forecasts"
PIPELINE_PATH = "app.jobs.sfms_run_pipeline"


class MockDailyForecastsDeps(NamedTuple):
    """Typed container for sfms_daily_forecasts mock dependencies."""

    db_session: MagicMock
    s3_client: MagicMock
    temp_processor: MagicMock
    rh_processor: MagicMock
    wind_speed_processor: MagicMock
    wind_direction_processor: MagicMock
    interpolation_processor: MagicMock
    fwi_processor: MagicMock
    wfwx_api: MagicMock
    addresser: MagicMock
    save_sfms_run: AsyncMock
    get_fuel_type_raster_by_year: AsyncMock


@pytest.fixture
def mock_dependencies(
    mocker: MockerFixture, mock_s3_client, mock_wfwx_api
) -> MockDailyForecastsDeps:
    """Mock external dependencies for run_sfms_daily_forecasts."""
    mocker.patch(f"{MODULE_PATH}.S3Client", return_value=mock_s3_client)
    mock_s3_client.all_objects_exist = AsyncMock(return_value=True)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(f"{MODULE_PATH}.ClientSession", return_value=mock_session)

    mock_wfwx_api.get_sfms_daily_forecasts_all_stations = AsyncMock(
        return_value=create_mock_sfms_actuals()
    )
    mocker.patch(f"{MODULE_PATH}.WfwxApi", return_value=mock_wfwx_api)

    mock_fuel_type_raster = MagicMock()
    mock_fuel_type_raster.object_store_path = "sfms/fuel/2024/fuel.tif"
    mock_get_fuel_type_raster_by_year = mocker.patch(
        f"{MODULE_PATH}.get_fuel_type_raster_by_year",
        new_callable=AsyncMock,
        return_value=mock_fuel_type_raster,
    )

    mock_read_session = MagicMock(spec=AsyncSession)

    @asynccontextmanager
    async def _read_scope():
        yield mock_read_session

    mocker.patch(f"{MODULE_PATH}.get_async_read_session_scope", _read_scope)

    mock_save_sfms_run = mocker.patch(
        f"{MODULE_PATH}.save_sfms_run", new_callable=AsyncMock, return_value=1
    )

    mock_addresser = MagicMock()
    mock_addresser.s3_prefix = "/vsis3/test-bucket"
    mocker.patch(f"{MODULE_PATH}.SFMSNGRasterAddresser", return_value=mock_addresser)

    mock_temp_processor = MagicMock(spec=TemperatureInterpolator)
    mock_temp_processor.process = AsyncMock(return_value="temperature.tif")
    mocker.patch(f"{PIPELINE_PATH}.TemperatureInterpolator", return_value=mock_temp_processor)

    mock_rh_processor = MagicMock(spec=RHInterpolator)
    mock_rh_processor.process = AsyncMock(return_value="relative_humidity.tif")
    mocker.patch(f"{PIPELINE_PATH}.RHInterpolator", return_value=mock_rh_processor)

    mock_wind_speed_processor = MagicMock(spec=WindSpeedInterpolator)
    mock_wind_speed_processor.process = AsyncMock(return_value="wind_speed.tif")
    mocker.patch(f"{PIPELINE_PATH}.WindSpeedInterpolator", return_value=mock_wind_speed_processor)

    mock_wind_direction_processor = MagicMock(spec=WindDirectionInterpolator)
    mock_wind_direction_processor.process = AsyncMock(return_value="wind_direction.tif")
    mocker.patch(
        f"{PIPELINE_PATH}.WindDirectionInterpolator",
        return_value=mock_wind_direction_processor,
    )

    mock_interpolation_processor = MagicMock(spec=Interpolator)
    mock_interpolation_processor.process = AsyncMock(return_value="precipitation.tif")
    mocker.patch(f"{PIPELINE_PATH}.Interpolator", return_value=mock_interpolation_processor)

    mock_fwi_processor = MagicMock(spec=FWIProcessor)
    mock_fwi_processor.calculate_index = AsyncMock(return_value=None)
    mocker.patch(f"{PIPELINE_PATH}.FWIProcessor", return_value=mock_fwi_processor)

    db_session = MagicMock(spec=AsyncSession)
    db_execute_result = MagicMock()
    db_execute_result.scalar = MagicMock(return_value=1)
    db_session.execute = AsyncMock(return_value=db_execute_result)
    db_session.get = AsyncMock(return_value=MagicMock())

    @asynccontextmanager
    async def _write_scope():
        yield db_session

    mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope", _write_scope)

    return MockDailyForecastsDeps(
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
        save_sfms_run=mock_save_sfms_run,
        get_fuel_type_raster_by_year=mock_get_fuel_type_raster_by_year,
    )


def test_forecast_datetimes_processes_next_three_days():
    target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)

    result = forecast_datetimes(target_date)

    assert result == [
        datetime(2024, 7, 5, 20, 0, tzinfo=timezone.utc),
        datetime(2024, 7, 6, 20, 0, tzinfo=timezone.utc),
        datetime(2024, 7, 7, 20, 0, tzinfo=timezone.utc),
    ]


class TestRunSfmsDailyForecasts:
    """Tests for run_sfms_daily_forecasts."""

    @pytest.mark.anyio
    async def test_runs_three_days(self, mock_dependencies: MockDailyForecastsDeps):
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        assert mock_dependencies.wfwx_api.get_sfms_daily_forecasts_all_stations.call_count == 3
        assert mock_dependencies.temp_processor.process.call_count == 3
        assert mock_dependencies.rh_processor.process.call_count == 3
        assert mock_dependencies.wind_speed_processor.process.call_count == 3
        assert mock_dependencies.wind_direction_processor.process.call_count == 3
        assert mock_dependencies.interpolation_processor.process.call_count == 3
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 18
        mock_dependencies.get_fuel_type_raster_by_year.assert_awaited_once()
        assert mock_dependencies.get_fuel_type_raster_by_year.call_args.args[1] == 2024

    @pytest.mark.anyio
    async def test_saves_forecast_runs(self, mock_dependencies: MockDailyForecastsDeps):
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        run_types = [call.args[1] for call in mock_dependencies.save_sfms_run.call_args_list]
        target_dates = [call.args[2] for call in mock_dependencies.save_sfms_run.call_args_list]
        assert run_types == [RunTypeEnum.forecast, RunTypeEnum.forecast, RunTypeEnum.forecast]
        assert [target_date.isoformat() for target_date in target_dates] == [
            "2024-07-05",
            "2024-07-06",
            "2024-07-07",
        ]

    @pytest.mark.anyio
    async def test_chains_fwi_seeds(self, mock_dependencies: MockDailyForecastsDeps):
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        base_seed_run_types = [
            call.kwargs["previous_base_run_type"]
            for call in mock_dependencies.addresser.get_fwi_inputs.call_args_list
            if call.args[1] in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC)
        ]
        assert base_seed_run_types[:3] == [RunType.ACTUAL, RunType.ACTUAL, RunType.ACTUAL]
        assert base_seed_run_types[3:] == [RunType.FORECAST] * 6

    @pytest.mark.anyio
    async def test_raises_on_empty_forecasts(self, mock_dependencies: MockDailyForecastsDeps):
        mock_dependencies.wfwx_api.get_sfms_daily_forecasts_all_stations = AsyncMock(
            return_value=[]
        )

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No station forecasts found"):
            await run_sfms_daily_forecasts(target_date)

        mock_dependencies.temp_processor.process.assert_not_called()

    @pytest.mark.anyio
    async def test_raises_when_previous_indices_missing(
        self, mock_dependencies: MockDailyForecastsDeps
    ):
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(return_value=False)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="Missing previous-day actual index rasters"):
            await run_sfms_daily_forecasts(target_date)

        mock_dependencies.fwi_processor.calculate_index.assert_not_called()


class TestMain:
    """Tests for main() entry point."""

    def test_main_with_valid_date(self, mocker: MockerFixture):
        mocker.patch.object(sys, "argv", ["sfms_daily_forecasts.py", "2025-07-15"])
        mock_run = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_forecasts", new_callable=AsyncMock)

        main()

        call_args = mock_run.call_args[0][0]
        assert call_args.year == 2025
        assert call_args.month == 7
        assert call_args.day == 15
        assert call_args.tzinfo == timezone.utc

    def test_main_without_date_uses_current(self, mocker: MockerFixture):
        mocker.patch.object(sys, "argv", ["sfms_daily_forecasts.py"])
        mock_now = datetime(2025, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        mocker.patch(f"{MODULE_PATH}.get_utc_now", return_value=mock_now)
        mock_run = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_forecasts", new_callable=AsyncMock)

        main()

        mock_run.assert_called_once_with(mock_now)

    def test_main_invalid_date_exits(self, mocker: MockerFixture):
        mocker.patch.object(sys, "argv", ["sfms_daily_forecasts.py", "not-a-date"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_job_exception_exits(self, mocker: MockerFixture):
        mocker.patch.object(sys, "argv", ["sfms_daily_forecasts.py", "2025-07-15"])
        exception = RuntimeError("job failed")
        mocker.patch(
            f"{MODULE_PATH}.run_sfms_daily_forecasts",
            new_callable=AsyncMock,
            side_effect=exception,
        )
        chatops_spy = mocker.spy(sys.modules[MODULE_PATH], "send_chatops_notification")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == os.EX_SOFTWARE
        chatops_spy.assert_called_once_with(
            "Encountered error running SFMS daily forecasts", exception
        )
