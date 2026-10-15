"""Unit tests for SFMS daily actuals job."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName, SFMSRunLogStatus
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import FBPParameter, FWIParameter

from app.jobs.sfms_daily_actuals import (
    is_fwi_interpolation_day,
    main,
    run_sfms_daily_actuals,
)
from app.jobs.sfms_run_pipeline import get_missing_fwi_seed_keys
from app.tests.jobs.sfms_daily_job_fixtures import (
    MockDailySFMSDeps,
    make_mock_daily_sfms_dependencies,
)

MODULE_PATH = "app.jobs.sfms_daily_actuals"
PIPELINE_PATH = "app.jobs.sfms_run_pipeline"


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


@pytest.fixture
def mock_dependencies(
    mocker: MockerFixture, monkeypatch, mock_s3_client, mock_wfwx_api
) -> MockDailySFMSDeps:
    """Use the shared daily-job dependencies for actuals tests."""
    return make_mock_daily_sfms_dependencies(
        mocker, monkeypatch, MODULE_PATH, mock_s3_client, mock_wfwx_api
    )


class TestRunSfmsDailyActuals:
    """Tests for run_sfms_daily_actuals."""

    @pytest.mark.anyio
    async def test_rejects_naive_target_date(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 4)

        with pytest.raises(AssertionError, match="timezone-aware"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.assert_not_called()

    @pytest.mark.anyio
    async def test_rejects_non_utc_target_date(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 4, tzinfo=timezone(timedelta(hours=-7)))

        with pytest.raises(AssertionError, match="not in UTC"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.assert_not_called()

    @pytest.mark.anyio
    async def test_runs_all_processors(self, mock_dependencies: MockDailySFMSDeps):
        """Test that all weather interpolation processors are called."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.rh_processor.process.assert_called_once()
        mock_dependencies.wind_speed_processor.process.assert_called_once()
        mock_dependencies.wind_direction_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()
        mock_dependencies.primary_fbp_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_fbp_uses_temporal_fuel_raster_for_target_date(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        await run_sfms_daily_actuals(datetime(2024, 7, 4, tzinfo=timezone.utc))

        mock_dependencies.run_temporal_fuel.assert_awaited_once()
        assert mock_dependencies.run_temporal_fuel.call_args.args[
            0
        ].datetime_to_process == datetime(2024, 7, 4, 20, tzinfo=timezone.utc)
        fbp_call = mock_dependencies.addresser.get_primary_fire_behaviour_inputs.call_args
        assert fbp_call.args[2] == "/vsis3/test-bucket/temporal/2024-07-04.tif"

    @pytest.mark.anyio
    async def test_processes_shared_fmc_for_target_date(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.addresser.get_fmc_inputs.assert_called_once_with(
            [target_date.date()],
            "/vsis3/test-bucket/sfms/fuel/2024/fuel.tif",
        )
        mock_dependencies.fmc_processor_class.assert_called_once_with(
            mock_dependencies.addresser,
        )
        mock_dependencies.fmc_processor.process.assert_awaited_once_with(
            mock_dependencies.s3_client,
            multi_wps_dataset_context,
            mock_dependencies.fmc_inputs,
        )

    @pytest.mark.anyio
    async def test_runs_processors_in_order(self, mock_dependencies: MockDailySFMSDeps):
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
    async def test_passes_s3_client_to_processors(self, mock_dependencies: MockDailySFMSDeps):
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
    async def test_sets_correct_hour(self, mock_dependencies: MockDailySFMSDeps):
        """Test that observations are processed at hour 20 (noon PDT)."""
        target_date = datetime(2024, 7, 4, hour=10, minute=30, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        dt = mock_dependencies.addresser.get_weather_key.call_args_list[0][0][0]
        assert dt.hour == 20
        assert dt.minute == 0
        assert dt.second == 0

    @pytest.mark.anyio
    async def test_raises_on_empty_actuals(self, mock_dependencies: MockDailySFMSDeps):
        """Test that run raises RuntimeError when no station data is found."""
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations = AsyncMock(return_value=[])

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No station observations found"):
            await run_sfms_daily_actuals(target_date)

    @pytest.mark.anyio
    async def test_writes_run_log_entries(self, mock_dependencies: MockDailySFMSDeps):
        """Test that run log records are added to the session."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # twelve tracked runs: 5 weather + 6 FWI + 1 primary FBP calculation
        assert mock_dependencies.db_session.execute.call_count == 12

    @pytest.mark.anyio
    async def test_logs_success_status(self, mock_dependencies: MockDailySFMSDeps):
        """Test that successful jobs are updated to success status."""
        records = [MagicMock() for _ in range(12)]
        mock_dependencies.db_session.get = AsyncMock(side_effect=records)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.db_session.get.call_count == 12
        for record in records:
            assert record.status == SFMSRunLogStatus.SUCCESS
            assert record.completed_at is not None

    @pytest.mark.anyio
    async def test_temperature_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailySFMSDeps
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
        # the sfms_run row was rolled back, so a manifest would have nothing to join to
        mock_dependencies.s3_client.put_object.assert_not_awaited()

    @pytest.mark.anyio
    async def test_temporal_fuel_failure_keeps_weather_and_fwi_and_raises(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        mock_dependencies.run_temporal_fuel.side_effect = RuntimeError("temporal fuel failed")

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temporal fuel failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 6
        mock_dependencies.primary_fbp_processor.process.assert_not_called()
        # weather and FWI committed before fuel failed
        mock_dependencies.db_session.commit.assert_awaited_once()
        mock_dependencies.s3_client.put_object.assert_awaited_once()
        failure_manifest = json.loads(
            mock_dependencies.s3_client.put_object.await_args.kwargs["body"]
        )
        assert failure_manifest["status"] == "failed"
        assert failure_manifest["failure_type"] == "RuntimeError"
        assert failure_manifest["failure_message"] == "temporal fuel failed"

    @pytest.mark.anyio
    async def test_precipitation_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailySFMSDeps
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

    @pytest.mark.anyio
    async def test_writes_run_manifest(self, mock_dependencies: MockDailySFMSDeps):
        """Test that the run's inputs and outputs are traced in a version 1 manifest."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # the manifest is the only object the job writes once every processor is mocked
        mock_dependencies.s3_client.put_object.assert_awaited_once()
        key = mock_dependencies.s3_client.put_object.await_args.kwargs["key"]
        payload = json.loads(mock_dependencies.s3_client.put_object.await_args.kwargs["body"])

        # the run datetime is the mocked "now", 2020-05-21T15:50:13Z
        assert key == ("sfms_ng/runs/2020/05/21/actual/2024-07-04_20200521T155013962000Z_run.json")
        assert payload["version"] == 1
        assert payload["run_type"] == "actual"
        assert payload["for_date"] == "2024-07-04"
        assert payload["run_datetime"] == "2020-05-21T15:50:13.962000Z"
        assert payload["input"]["station_codes"] == [100, 101]
        # the temporal fuel raster is recorded by run_temporal_fuel, which is mocked here
        assert payload["input"]["fuel_raster"] == {
            "base": "sfms/fuel/2024/fuel.tif",
            "pc": "sfms/static/m12_2024.tif",
        }
        assert payload["input"]["seed_rasters"] == {
            "ffmc": "sfms_ng/actual/2024/07/03/ffmc_20240703.tif",
            "dmc": "sfms_ng/actual/2024/07/03/dmc_20240703.tif",
            "dc": "sfms_ng/actual/2024/07/03/dc_20240703.tif",
        }
        assert payload["input"]["static_rasters"] == {
            "dem": "sfms/static/bc_elevation.tif",
            "mask": "sfms/static/bc_mask.tif",
            "slope": "sfms_ng/static/bc_slope.tif",
            "aspect": "sfms_ng/static/bc_aspect.tif",
            "elevation": "sfms_ng/static/bc_elevation.tif",
            "latitude": "sfms_ng/static/latitude.tif",
            "longitude": "sfms_ng/static/longitude.tif",
        }
        assert payload["input"]["fmc_raster"] == "sfms_ng/static/fmc/2024/07/04/fmc_20240704.tif"
        assert payload["output"]["weather"]["temperature"] == (
            "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
        )
        assert payload["output"]["fwi"]["fwi"] == "sfms_ng/actual/2024/07/04/fwi_20240704.tif"
        assert payload["output"]["fbp"]["hfi"] == "sfms_ng/actual/2024/07/04/hfi_20240704.tif"
        assert payload["output"]["fmc_raster"] == "sfms_ng/static/fmc/2024/07/04/fmc_20240704.tif"

    @pytest.mark.anyio
    async def test_writes_run_manifest_without_fuel_when_fwi_is_skipped(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """A run that stops after weather traces no fuel, FWI or FBP outputs."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(return_value=False)

        await run_sfms_daily_actuals(target_date)

        payload = json.loads(mock_dependencies.s3_client.put_object.await_args.kwargs["body"])
        assert payload["output"]["weather"]["temperature"] == (
            "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
        )
        assert payload["output"]["fwi"] == {}
        assert payload["output"]["fbp"] == {}
        assert "fuel_raster" not in payload["output"]
        assert payload["input"]["seed_rasters"] == {}
        assert payload["status"] == "failed"
        assert payload["failed_stage"] == "fwi_seed_check"
        mock_dependencies.run_temporal_fuel.assert_not_awaited()


class TestMondayFWIInterpolation:
    """Tests for Monday FWI index interpolation."""

    @pytest.mark.anyio
    async def test_first_monday_may_runs_fwi_interpolation(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """Test that FWI interpolation runs on the first Monday of May."""
        # 2024-05-06 is the first Monday of May 2024
        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 base FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 3

    @pytest.mark.anyio
    async def test_first_monday_april_runs_fwi_interpolation(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """Test that FWI interpolation runs on the first Monday of April."""
        # 2024-04-01 is the first Monday of April 2024
        target_date = datetime(2024, 4, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 base FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 3

    @pytest.mark.anyio
    async def test_non_monday_skips_fwi_interpolation(self, mock_dependencies: MockDailySFMSDeps):
        """Test that FWI interpolation does NOT run on non-Mondays."""
        # 2024-07-04 is a Thursday
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # Only temp + RH + precip, no FWI
        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()

    @pytest.mark.anyio
    async def test_monday_outside_april_may_skips_fwi_interpolation(
        self, mock_dependencies: MockDailySFMSDeps
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
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """Test that FWI interpolation runs on the second Monday of April."""
        # 2024-04-08 is the second Monday of April 2024
        target_date = datetime(2024, 4, 8, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # temp processor called once, IDW processor called 4 times (1 precip + 3 base FWI)
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.interpolation_processor.process.call_count == 4
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 3

    @pytest.mark.anyio
    async def test_monday_april_writes_twelve_run_log_entries(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """Test that a Monday in April produces 12 run log entries."""
        # 2024-04-01 is the first Monday of April 2024
        target_date = datetime(2024, 4, 1, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        # twelve tracked runs: 5 weather + 3 interpolated FWI + 3 derived FWI + 1 primary FBP
        assert mock_dependencies.db_session.execute.call_count == 12


class TestFWICalculationVsInterpolation:
    """Regression tests: FWI interpolation and FWI calculation are mutually exclusive."""

    @pytest.mark.anyio
    async def test_monday_interpolation_skips_fwi_calculation(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """On a re-interpolation Monday, only derived FWI calculations should run."""
        # 2024-05-06 is the first Monday of May 2024
        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        actual_fwi_params = [
            call.args[1] for call in mock_dependencies.addresser.get_fwi_inputs.call_args_list
        ]
        assert actual_fwi_params == [
            FWIParameter.ISI,
            FWIParameter.BUI,
            FWIParameter.FWI,
        ]
        mock_dependencies.s3_client.object_exists.assert_awaited_once()

    @pytest.mark.anyio
    async def test_regular_day_runs_fwi_calculation_not_interpolation(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """On a regular day, FWI calculation runs and FWI interpolation does not."""
        # 2024-07-04 is a Thursday
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.fwi_processor.calculate_index.call_count == 6
        # Each calculator must use its own FWIParameter — a wiring bug where calls
        # share the same fwi_param would silently produce wrong rasters.
        actual_fwi_params = [
            call.args[1] for call in mock_dependencies.addresser.get_fwi_inputs.call_args_list
        ]
        assert actual_fwi_params == [
            FWIParameter.FFMC,
            FWIParameter.DMC,
            FWIParameter.DC,
            FWIParameter.ISI,
            FWIParameter.BUI,
            FWIParameter.FWI,
        ]
        # IDW called once only for precip, not for FWI indices
        mock_dependencies.interpolation_processor.process.assert_called_once()

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("missing_param", "expected_missing"),
        [
            (FWIParameter.FFMC, ["ffmc=actual_ffmc_20240703.tif"]),
            (FWIParameter.DMC, ["dmc=actual_dmc_20240703.tif"]),
            (FWIParameter.DC, ["dc=actual_dc_20240703.tif"]),
        ],
    )
    async def test_get_missing_fwi_seed_keys_returns_only_missing_keys(
        self,
        mock_dependencies: MockDailySFMSDeps,
        missing_param: FWIParameter,
        expected_missing: list[str],
    ):
        """Previous-day seed checks should report only the missing FFMC/DMC/DC key."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        mock_dependencies.addresser.get_index_key.side_effect = lambda dt, param, run_type: (
            f"{run_type.value}_{param.value}_{dt.strftime('%Y%m%d')}.tif"
        )

        async def fake_all_objects_exist(*keys):
            return all(f"actual_{missing_param.value}_20240703.tif" not in str(key) for key in keys)

        mock_dependencies.s3_client.all_objects_exist = AsyncMock(
            side_effect=fake_all_objects_exist
        )

        missing = await get_missing_fwi_seed_keys(
            target_date,
            mock_dependencies.addresser,
            mock_dependencies.s3_client,
        )

        assert missing == expected_missing

    @pytest.mark.anyio
    async def test_regular_day_skips_fwi_calculation_when_previous_indices_missing(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """On a regular day, missing previous-day seed rasters should skip FWI gracefully."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(return_value=False)

        await run_sfms_daily_actuals(target_date)

        mock_dependencies.fwi_processor.calculate_index.assert_not_called()
        mock_dependencies.run_temporal_fuel.assert_not_awaited()
        mock_dependencies.primary_fbp_processor.process.assert_not_called()
        # Only weather interpolation jobs are tracked when the FWI chain is skipped.
        assert mock_dependencies.db_session.execute.call_count == 5

    @pytest.mark.anyio
    async def test_regular_day_tracks_expected_job_names_in_order(
        self, mock_dependencies: MockDailySFMSDeps, mocker: MockerFixture
    ):
        """Regular-day runs should track the full weather + FWI job names in order."""
        captured_job_names = []

        async def fake_run_tracked_job(job_name, sfms_run_id, session, action):
            captured_job_names.append(job_name)
            return await action()

        mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=fake_run_tracked_job)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert captured_job_names == [
            SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            SFMSRunLogJobName.RH_INTERPOLATION,
            SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            SFMSRunLogJobName.FFMC_CALCULATION,
            SFMSRunLogJobName.DMC_CALCULATION,
            SFMSRunLogJobName.DC_CALCULATION,
            SFMSRunLogJobName.ISI_CALCULATION,
            SFMSRunLogJobName.BUI_CALCULATION,
            SFMSRunLogJobName.FWI_CALCULATION,
            SFMSRunLogJobName.PRIMARY_FBP_CALCULATION,
        ]

    @pytest.mark.anyio
    async def test_interpolation_monday_tracks_expected_job_names_in_order(
        self, mock_dependencies: MockDailySFMSDeps, mocker: MockerFixture
    ):
        """Interpolation Mondays should track interpolation/calculation job names in order."""
        captured_job_names = []

        async def fake_run_tracked_job(job_name, sfms_run_id, session, action):
            captured_job_names.append(job_name)
            return await action()

        mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=fake_run_tracked_job)

        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert captured_job_names == [
            SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            SFMSRunLogJobName.RH_INTERPOLATION,
            SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            SFMSRunLogJobName.FFMC_INTERPOLATION,
            SFMSRunLogJobName.DMC_INTERPOLATION,
            SFMSRunLogJobName.DC_INTERPOLATION,
            SFMSRunLogJobName.ISI_CALCULATION,
            SFMSRunLogJobName.BUI_CALCULATION,
            SFMSRunLogJobName.FWI_CALCULATION,
            SFMSRunLogJobName.PRIMARY_FBP_CALCULATION,
        ]


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
        exception = RuntimeError("job failed")
        mocker.patch(
            f"{MODULE_PATH}.run_sfms_daily_actuals",
            new_callable=AsyncMock,
            side_effect=exception,
        )
        chatops_spy = mocker.spy(sys.modules[MODULE_PATH], "send_chatops_notification")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == os.EX_SOFTWARE
        chatops_spy.assert_called_once_with(
            "Encountered error running SFMS daily actuals", exception
        )
