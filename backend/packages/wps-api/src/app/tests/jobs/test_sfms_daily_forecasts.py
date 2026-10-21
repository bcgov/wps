"""Unit tests for SFMS daily forecasts job."""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, call

import pytest
from pytest_mock import MockerFixture
from wps_sfms.processors.foliar_moisture_content import FoliarMoistureContentKeys
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import FWIParameter

from app.jobs.sfms_daily_forecasts import (
    expected_actual_target_date,
    forecast_datetimes,
    main,
    run_datetime_for_cli_date,
    run_sfms_daily_forecasts,
)
from app.tests.jobs.sfms_daily_job_fixtures import (
    MockDailySFMSDeps,
    fmc_key,
    make_mock_daily_sfms_dependencies,
)

MODULE_PATH = "app.jobs.sfms_daily_forecasts"


@pytest.fixture
def mock_dependencies(
    mocker: MockerFixture, monkeypatch, mock_s3_client, mock_wfwx_api
) -> MockDailySFMSDeps:
    """Use the shared daily-job dependencies for forecast tests."""
    return make_mock_daily_sfms_dependencies(
        mocker, monkeypatch, MODULE_PATH, mock_s3_client, mock_wfwx_api
    )


def test_forecast_datetimes_processes_next_three_days():
    seed_actual_date = date(2024, 7, 4)

    result = forecast_datetimes(seed_actual_date)

    assert result == [
        datetime(2024, 7, 5, 20, 0, tzinfo=timezone.utc),
        datetime(2024, 7, 6, 20, 0, tzinfo=timezone.utc),
        datetime(2024, 7, 7, 20, 0, tzinfo=timezone.utc),
    ]


def test_expected_actual_target_date_uses_yesterday_before_actuals_available():
    run_datetime = datetime(2024, 7, 4, 15, 0, tzinfo=timezone.utc)

    result = expected_actual_target_date(run_datetime)

    assert result == date(2024, 7, 3)


def test_expected_actual_target_date_uses_today_after_actuals_available():
    run_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

    result = expected_actual_target_date(run_datetime)

    assert result == date(2024, 7, 4)


def test_expected_actual_target_date_rejects_naive_datetime():
    naive_datetime = datetime(2024, 7, 4)

    with pytest.raises(AssertionError, match="timezone-aware"):
        expected_actual_target_date(naive_datetime)


def test_run_datetime_for_cli_date_uses_current_pdt_time():
    current_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

    result = run_datetime_for_cli_date(date(2024, 7, 4), current_datetime)

    assert result == datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)


def test_run_datetime_for_cli_date_before_actuals_available():
    current_datetime = datetime(2024, 7, 5, 15, 30, tzinfo=timezone.utc)

    result = run_datetime_for_cli_date(date(2024, 7, 4), current_datetime)

    assert result == datetime(2024, 7, 4, 15, 30, tzinfo=timezone.utc)


class TestRunSfmsDailyForecasts:
    """Tests for run_sfms_daily_forecasts."""

    @pytest.mark.anyio
    async def test_runs_three_days(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        assert mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.call_count == 3
        assert mock_dependencies.temp_processor.process.call_count == 3
        assert mock_dependencies.rh_processor.process.call_count == 3
        assert mock_dependencies.wind_speed_processor.process.call_count == 3
        assert mock_dependencies.wind_direction_processor.process.call_count == 3
        assert mock_dependencies.interpolation_processor.process.call_count == 3
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 18
        assert mock_dependencies.primary_fbp_processor.process.call_count == 3
        mock_dependencies.get_fuel_type_raster_by_year.assert_awaited_once()
        assert mock_dependencies.get_fuel_type_raster_by_year.call_args.args[1] == 2024

    @pytest.mark.anyio
    async def test_first_date_failure_stops_the_batch(self, mock_dependencies: MockDailySFMSDeps):
        mock_dependencies.find_temporal_fuel.side_effect = RuntimeError("temporal fuel failed")

        run_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="temporal fuel failed"):
            await run_sfms_daily_forecasts(run_datetime)

        # only the first date started: later dates seed from it, so they don't run
        mock_dependencies.save_sfms_run.assert_awaited_once()
        mock_dependencies.temp_processor.process.assert_called_once()
        assert mock_dependencies.fwi_processor.calculate_index.call_count == 6
        mock_dependencies.primary_fbp_processor.process.assert_not_called()
        manifest = json.loads(mock_dependencies.s3_client.put_object.await_args.kwargs["body"])
        assert manifest["for_date"] == "2024-07-05"
        assert manifest["status"] == "failed"
        assert manifest["failed_step"] == "temporal_fuel"
        assert manifest["failure_message"] == "temporal fuel failed"

    @pytest.mark.anyio
    async def test_later_date_failure_keeps_earlier_dates_and_skips_later_ones(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        succeed = mock_dependencies.find_temporal_fuel.side_effect

        def fail_on_second_date(session, target_date, *args, **hashes):
            if target_date.day == 6:
                raise RuntimeError("temporal fuel failed")
            return succeed(session, target_date, *args, **hashes)

        mock_dependencies.find_temporal_fuel.side_effect = fail_on_second_date

        run_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)
        with pytest.raises(RuntimeError, match="temporal fuel failed"):
            await run_sfms_daily_forecasts(run_datetime)

        assert mock_dependencies.save_sfms_run.await_count == 2
        statuses = {
            manifest["for_date"]: manifest["status"]
            for manifest in (
                json.loads(call.kwargs["body"])
                for call in mock_dependencies.s3_client.put_object.await_args_list
                if call.kwargs["key"].startswith("sfms_ng/runs/")
            )
        }
        assert statuses == {"2024-07-05": "success", "2024-07-06": "failed"}

    @pytest.mark.anyio
    async def test_fbp_uses_temporal_fuel_raster_per_forecast_date(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        await run_sfms_daily_forecasts(datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc))

        fbp_fuel_paths = [
            call.args[2]
            for call in mock_dependencies.addresser.get_primary_fire_behaviour_inputs.call_args_list
        ]
        assert fbp_fuel_paths == [
            "/vsis3/test-bucket/temporal/2024-07-05.tif",
            "/vsis3/test-bucket/temporal/2024-07-06.tif",
            "/vsis3/test-bucket/temporal/2024-07-07.tif",
        ]

    @pytest.mark.anyio
    async def test_processes_fmc_for_each_forecast_date(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        assert mock_dependencies.addresser.get_fmc_inputs.call_args_list == [
            call([for_date], "/vsis3/test-bucket/sfms/fuel/2024/fuel.tif")
            for for_date in (date(2024, 7, 5), date(2024, 7, 6), date(2024, 7, 7))
        ]
        assert (
            mock_dependencies.fmc_processor.process.await_args_list
            == [
                call(
                    mock_dependencies.s3_client,
                    multi_wps_dataset_context,
                    mock_dependencies.fmc_inputs,
                )
            ]
            * 3
        )

    @pytest.mark.anyio
    async def test_records_fmc_as_output_or_reused_per_forecast_date(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        # 07-05's FMC is new, while 07-06 and 07-07 were calculated by an earlier forecast run
        calculated = {date(2024, 7, 5)}
        fmc_dates = iter((date(2024, 7, 5), date(2024, 7, 6), date(2024, 7, 7)))

        def process(*_args) -> FoliarMoistureContentKeys:
            target_date = next(fmc_dates)
            keys = {target_date: fmc_key(target_date)}
            if target_date in calculated:
                return FoliarMoistureContentKeys(processed_keys=keys, reused_keys={})
            return FoliarMoistureContentKeys(processed_keys={}, reused_keys=keys)

        mock_dependencies.fmc_processor.process.side_effect = process

        await run_sfms_daily_forecasts(datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc))

        manifests = {
            manifest["for_date"]: manifest
            for manifest in (
                json.loads(call.kwargs["body"])
                for call in mock_dependencies.s3_client.put_object.await_args_list
                if call.kwargs["key"].startswith("sfms_ng/runs/")
            )
        }
        assert manifests["2024-07-05"]["output"]["fmc_raster"] == fmc_key(date(2024, 7, 5))
        assert "fmc_raster" not in manifests["2024-07-05"]["reused"]
        for reused_date in (date(2024, 7, 6), date(2024, 7, 7)):
            manifest = manifests[reused_date.isoformat()]
            assert manifest["reused"]["fmc_raster"] == fmc_key(reused_date)
            assert "fmc_raster" not in manifest["output"]
            # FBP still read the reused raster
            assert manifest["input"]["fmc_raster"] == fmc_key(reused_date)

    @pytest.mark.anyio
    async def test_saves_forecast_runs(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

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
    async def test_forecasts_from_expected_successful_actual(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        run_datetime = datetime(2024, 7, 4, 15, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(run_datetime)

        requested_datetimes = [
            call.args[0]
            for call in mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.call_args_list
        ]
        assert requested_datetimes == [
            datetime(2024, 7, 4, 20, 0, tzinfo=timezone.utc),
            datetime(2024, 7, 5, 20, 0, tzinfo=timezone.utc),
            datetime(2024, 7, 6, 20, 0, tzinfo=timezone.utc),
        ]

    @pytest.mark.anyio
    async def test_chains_fwi_seeds(self, mock_dependencies: MockDailySFMSDeps):
        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        # the run type of the seed raster each FFMC, DMC and DC calculation was handed
        seed_run_types = [
            call.args[4][call.args[1]].split("/")[1]
            for call in mock_dependencies.addresser.get_fwi_inputs.call_args_list
            if call.args[1] in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC)
        ]
        assert seed_run_types[:3] == ["actual"] * 3
        assert seed_run_types[3:] == ["forecast"] * 6

    @pytest.mark.anyio
    async def test_writes_a_manifest_per_forecast_date(self, mock_dependencies: MockDailySFMSDeps):
        # each forecast date saves its own sfms_run row
        mock_dependencies.save_sfms_run.side_effect = [11, 12, 13]
        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        await run_sfms_daily_forecasts(target_date)

        manifest_calls = [
            call
            for call in mock_dependencies.s3_client.put_object.await_args_list
            if call.kwargs["key"].startswith("sfms_ng/runs/")
        ]
        # one manifest per forecast date, each in its forecast date folder
        keys = sorted(call.kwargs["key"] for call in manifest_calls)
        assert keys == [
            "sfms_ng/runs/forecast/2024/07/05/target-2024-07-05_run-2020-05-21T15-50-13.962000Z.json",
            "sfms_ng/runs/forecast/2024/07/06/target-2024-07-06_run-2020-05-21T15-50-13.962000Z.json",
            "sfms_ng/runs/forecast/2024/07/07/target-2024-07-07_run-2020-05-21T15-50-13.962000Z.json",
        ]
        payloads = [json.loads(call.kwargs["body"]) for call in manifest_calls]
        assert {payload["for_date"]: payload["sfms_run_id"] for payload in payloads} == {
            "2024-07-05": 11,
            "2024-07-06": 12,
            "2024-07-07": 13,
        }
        payload = payloads[0]
        assert payload["run_type"] == "forecast"
        assert payload["for_date"] == "2024-07-05"
        assert payload["input"]["station_codes"] == [100, 101]
        assert payload["input"]["fuel_raster"]["base"] == "sfms/fuel/2024/fuel.tif"
        # the first forecast day seeds from the previous actual run's rasters
        assert payload["input"]["seed_rasters"] == {
            "ffmc": "sfms_ng/actual/2024/07/04/ffmc_20240704.tif",
            "dmc": "sfms_ng/actual/2024/07/04/dmc_20240704.tif",
            "dc": "sfms_ng/actual/2024/07/04/dc_20240704.tif",
        }
        assert payload["input"]["fmc_raster"] == "sfms_ng/static/fmc/2024/07/05/fmc_20240705.tif"
        assert payload["output"]["weather"]["temperature"] == (
            "sfms_ng/forecast/2024/07/05/temperature_20240705.tif"
        )
        assert payload["output"]["danger_rating_raster"] == (
            "sfms_ng/forecast/2024/07/05/danger_rating_20240705.tif"
        )
        assert payload["output"]["fbp"]["hfi"] == "sfms_ng/forecast/2024/07/05/hfi_20240705.tif"

    @pytest.mark.anyio
    async def test_raises_when_no_fuel_type_raster_for_the_year(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        mock_dependencies.get_fuel_type_raster_by_year.return_value = None
        run_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No fuel type raster found for 2024"):
            await run_sfms_daily_forecasts(run_datetime)

        # fails before any forecast is fetched or run saved
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.assert_not_called()
        mock_dependencies.save_sfms_run.assert_not_awaited()
        mock_dependencies.s3_client.put_object.assert_not_awaited()

    @pytest.mark.anyio
    async def test_date_missing_its_forecast_seeds_records_it_and_stops_the_batch(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        """A date whose previous-day forecast seeds vanished mid-run fails the batch."""
        # the actual seeds exist, so the batch starts, but the first date's forecast
        # rasters, which the second date seeds from, are missing
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(
            side_effect=lambda *keys: not any("forecast/2024/07/05" in key for key in keys)
        )
        run_datetime = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        with pytest.raises(
            RuntimeError, match="Missing previous-day seeds for forecast 2024-07-06"
        ):
            await run_sfms_daily_forecasts(run_datetime)

        manifests = {
            manifest["for_date"]: manifest
            for manifest in (
                json.loads(call.kwargs["body"])
                for call in mock_dependencies.s3_client.put_object.await_args_list
                if call.kwargs["key"].startswith("sfms_ng/runs/")
            )
        }
        assert manifests["2024-07-06"]["status"] == "failed"
        assert manifests["2024-07-06"]["failed_step"] == "fwi_seed_check"
        assert manifests["2024-07-06"]["output"]["fbp"] == {}
        assert manifests["2024-07-05"]["status"] == "success"
        # only the first date got FBP, and the third date never started
        assert "2024-07-07" not in manifests
        assert mock_dependencies.primary_fbp_processor.process.await_count == 1

    @pytest.mark.anyio
    async def test_raises_on_empty_forecasts(self, mock_dependencies: MockDailySFMSDeps):
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations = AsyncMock(return_value=[])

        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="No station forecasts found"):
            await run_sfms_daily_forecasts(target_date)

        mock_dependencies.temp_processor.process.assert_not_called()
        # no sfms_run row was committed, so a manifest would have nothing to join to
        mock_dependencies.s3_client.put_object.assert_not_awaited()

    @pytest.mark.anyio
    async def test_raises_when_actual_seed_rasters_missing(
        self, mock_dependencies: MockDailySFMSDeps
    ):
        mock_dependencies.s3_client.all_objects_exist = AsyncMock(return_value=False)

        target_date = datetime(2024, 7, 5, 0, 45, tzinfo=timezone.utc)

        with pytest.raises(RuntimeError, match="Missing actual seed rasters for 2024-07-04"):
            await run_sfms_daily_forecasts(target_date)

        mock_dependencies.get_fuel_type_raster_by_year.assert_not_called()
        mock_dependencies.wfwx_api.get_sfms_daily_weather_all_stations.assert_not_called()
        mock_dependencies.fwi_processor.calculate_index.assert_not_called()

    @pytest.mark.anyio
    async def test_rejects_naive_run_datetime(self, mock_dependencies: MockDailySFMSDeps):
        run_datetime = datetime(2024, 7, 4)

        with pytest.raises(AssertionError, match="timezone-aware"):
            await run_sfms_daily_forecasts(run_datetime)

    @pytest.mark.anyio
    async def test_rejects_non_utc_run_datetime(self, mock_dependencies: MockDailySFMSDeps):
        run_datetime = datetime(2024, 7, 4, tzinfo=timezone(timedelta(hours=-7)))

        with pytest.raises(AssertionError, match="not in UTC"):
            await run_sfms_daily_forecasts(run_datetime)


class TestMain:
    """Tests for main() entry point."""

    def test_main_with_valid_date(self, mocker: MockerFixture):
        mocker.patch.object(sys, "argv", ["sfms_daily_forecasts.py", "2025-07-15"])
        mock_now = datetime(2025, 7, 16, 0, 45, tzinfo=timezone.utc)
        mocker.patch(f"{MODULE_PATH}.get_utc_now", return_value=mock_now)
        mock_run = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_forecasts", new_callable=AsyncMock)

        main()

        call_args = mock_run.call_args[0][0]
        assert call_args == run_datetime_for_cli_date(date(2025, 7, 15), mock_now)

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
