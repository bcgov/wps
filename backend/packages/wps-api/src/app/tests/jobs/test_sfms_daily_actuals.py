"""Unit tests for SFMS daily actuals job."""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName, SFMSRunLogStatus
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import FWIParameter

from app.jobs.sfms_daily_actuals import (
    is_fwi_interpolation_day,
    main,
    run_sfms_daily_actuals,
)
from app.tests.jobs.sfms_daily_job_fixtures import (
    MockDailySFMSDeps,
    make_mock_daily_sfms_dependencies,
)

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
    async def test_fbp_uses_temporal_fuel_raster_for_target_date(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        await run_sfms_daily_actuals(datetime(2024, 7, 4, tzinfo=timezone.utc))

        mock_dependencies.find_temporal_fuel.assert_awaited_once()
        assert mock_dependencies.find_temporal_fuel.call_args.args[1] == date(2024, 7, 4)
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
    async def test_raises_when_no_fuel_type_raster_for_the_year(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        mock_dependencies.get_fuel_type_raster_by_year.return_value = None
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No fuel type raster found for 2024"):
            await run_sfms_daily_actuals(target_date)

        # fails before observations are fetched or a run is saved
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.assert_not_called()
        mock_dependencies.save_sfms_run.assert_not_awaited()

    @pytest.mark.anyio
    async def test_raises_on_empty_actuals(self, mock_dependencies: MockDailySFMSDeps):
        """Test that run raises RuntimeError when no station data is found."""
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations = AsyncMock(return_value=[])

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No station observations found"):
            await run_sfms_daily_actuals(target_date)

    @pytest.mark.anyio
    async def test_logs_success_status(self, mock_dependencies: MockDailySFMSDeps):
        """Test that successful jobs are updated to success status."""
        records = [MagicMock() for _ in range(15)]
        mock_dependencies.db_session.get = AsyncMock(side_effect=records)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert mock_dependencies.db_session.get.call_count == 15
        for record in records:
            assert record.status == SFMSRunLogStatus.SUCCESS
            assert record.completed_at is not None

    @pytest.mark.anyio
    async def test_temperature_failure_logs_failed_and_raises(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """A failed job's FAILED log row and the run's failure manifest persist, then it raises."""
        mock_dependencies.temp_processor.process = AsyncMock(
            side_effect=RuntimeError("temp failed")
        )
        run_logs = [MagicMock(), MagicMock()]
        mock_dependencies.db_session.get = AsyncMock(side_effect=run_logs)

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temp failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.rh_processor.process.assert_not_called()
        mock_dependencies.wind_speed_processor.process.assert_not_called()
        mock_dependencies.wind_direction_processor.process.assert_not_called()
        mock_dependencies.interpolation_processor.process.assert_not_called()
        # FMC succeeded before temperature failed; each log row commits on its own
        assert [log.status for log in run_logs] == [
            SFMSRunLogStatus.SUCCESS,
            SFMSRunLogStatus.FAILED,
        ]
        # the sfms_run row was committed first, so the failure manifest can be joined to it
        manifest = json.loads(mock_dependencies.s3_client.put_object.await_args.kwargs["body"])
        assert manifest["status"] == "failed"
        assert manifest["failed_step"] == "temperature_interpolation"
        # recorded when the run started, so a run that fails early still has them
        assert manifest["input"]["station_codes"] == [100, 101]
        assert manifest["input"]["fuel_raster"]["base"] == "sfms/fuel/2024/fuel.tif"

    @pytest.mark.anyio
    async def test_failed_manifest_upload_alerts_without_failing_the_run(
        self, mock_dependencies: MockDailySFMSDeps, mocker: MockerFixture
    ):
        """A run whose rasters were all written completes even when its manifest can't be."""
        chatops = mocker.patch("wps_sfms.run_context.send_chatops_notification")
        mock_dependencies.s3_client.put_object = AsyncMock(side_effect=RuntimeError("s3 down"))

        await run_sfms_daily_actuals(datetime(2024, 7, 4, tzinfo=timezone.utc))

        mock_dependencies.primary_fbp_processor.process.assert_awaited_once()
        chatops.assert_called_once()
        assert "manifest" in chatops.call_args.args[0]

    @pytest.mark.anyio
    async def test_failed_manifest_upload_does_not_mask_the_step_failure(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """The job raises the step's error even when its failure manifest can't be written."""
        mock_dependencies.temp_processor.process = AsyncMock(
            side_effect=RuntimeError("temp failed")
        )
        mock_dependencies.s3_client.put_object = AsyncMock(side_effect=RuntimeError("s3 down"))
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temp failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.s3_client.put_object.assert_awaited_once()

    @pytest.mark.anyio
    async def test_temporal_fuel_failure_records_the_failed_run_and_raises(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        mock_dependencies.find_temporal_fuel.side_effect = RuntimeError("temporal fuel failed")

        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temporal fuel failed"):
            await run_sfms_daily_actuals(target_date)

        mock_dependencies.temp_processor.process.assert_called_once()
        mock_dependencies.interpolation_processor.process.assert_called_once()
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 6
        mock_dependencies.primary_fbp_processor.process.assert_not_called()
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
        assert key == (
            "sfms_ng/runs/actual/2024/07/04/target-2024-07-04_run-2020-05-21T15-50-13.962000Z.json"
        )
        assert payload["version"] == 1
        # the id save_sfms_run returned for the run
        assert payload["sfms_run_id"] == 1
        assert payload["run_type"] == "actual"
        assert payload["for_date"] == "2024-07-04"
        assert payload["run_datetime"] == "2020-05-21T15:50:13.962000Z"
        assert payload["input"]["station_codes"] == [100, 101]
        assert payload["input"]["fuel_raster"] == {
            "base": "sfms/fuel/2024/fuel.tif",
            "temporal": "temporal/2024-07-04.tif",
            "percent_conifer": "sfms/static/m12_2024.tif",
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
        assert payload["output"]["danger_rating_raster"] == (
            "sfms_ng/actual/2024/07/04/danger_rating_20240704.tif"
        )
        assert payload["output"]["fbp"]["hfi"] == "sfms_ng/actual/2024/07/04/hfi_20240704.tif"
        assert payload["output"]["fmc_raster"] == "sfms_ng/static/fmc/2024/07/04/fmc_20240704.tif"
        # the fixture's temporal fuel grid already exists, so the run reuses it
        assert payload["reused"] == {"fuel_raster": "temporal/2024-07-04.tif"}

    @pytest.mark.anyio
    async def test_skips_fwi_fuel_and_fbp_when_seeds_are_missing(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """A run without previous-day seeds stops after weather, and its manifest says so."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(return_value=False)

        await run_sfms_daily_actuals(target_date)

        payload = json.loads(mock_dependencies.s3_client.put_object.await_args.kwargs["body"])
        assert payload["output"]["weather"]["temperature"] == (
            "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
        )
        assert payload["output"]["danger_rating_raster"] == (
            "sfms_ng/actual/2024/07/04/danger_rating_20240704.tif"
        )
        assert payload["output"]["fwi"] == {}
        assert payload["output"]["fbp"] == {}
        assert "fuel_raster" not in payload["output"]
        assert payload["input"]["seed_rasters"] == {}
        assert payload["status"] == "failed"
        assert payload["failed_step"] == "fwi_seed_check"
        mock_dependencies.fwi_processor.calculate_index.assert_not_called()
        mock_dependencies.find_temporal_fuel.assert_not_awaited()
        mock_dependencies.primary_fbp_processor.process.assert_not_called()


class TestFWIBranches:
    """A run either re-interpolates FWI (April/May Mondays) or calculates it forward from seeds."""

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
    async def test_regular_day_tracks_expected_job_names_in_order(
        self, mock_dependencies: MockDailySFMSDeps, tracked_jobs
    ):
        """Regular-day runs should track the full weather + FWI job names in order."""
        target_date = datetime(2024, 7, 4, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert tracked_jobs == [
            SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT,
            SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            SFMSRunLogJobName.RH_INTERPOLATION,
            SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            SFMSRunLogJobName.DANGER_RATING_INTERPOLATION,
            SFMSRunLogJobName.FFMC_CALCULATION,
            SFMSRunLogJobName.DMC_CALCULATION,
            SFMSRunLogJobName.DC_CALCULATION,
            SFMSRunLogJobName.ISI_CALCULATION,
            SFMSRunLogJobName.BUI_CALCULATION,
            SFMSRunLogJobName.FWI_CALCULATION,
            SFMSRunLogJobName.TEMPORAL_FUEL,
            SFMSRunLogJobName.PRIMARY_FBP_CALCULATION,
        ]

    @pytest.mark.anyio
    async def test_interpolation_monday_tracks_expected_job_names_in_order(
        self, mock_dependencies: MockDailySFMSDeps, tracked_jobs
    ):
        """Interpolation Mondays should track interpolation/calculation job names in order."""
        target_date = datetime(2024, 5, 6, tzinfo=timezone.utc)
        await run_sfms_daily_actuals(target_date)

        assert tracked_jobs == [
            SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT,
            SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            SFMSRunLogJobName.RH_INTERPOLATION,
            SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            SFMSRunLogJobName.DANGER_RATING_INTERPOLATION,
            SFMSRunLogJobName.FFMC_INTERPOLATION,
            SFMSRunLogJobName.DMC_INTERPOLATION,
            SFMSRunLogJobName.DC_INTERPOLATION,
            SFMSRunLogJobName.ISI_CALCULATION,
            SFMSRunLogJobName.BUI_CALCULATION,
            SFMSRunLogJobName.FWI_CALCULATION,
            SFMSRunLogJobName.TEMPORAL_FUEL,
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
