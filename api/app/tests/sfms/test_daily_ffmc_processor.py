from contextlib import ExitStack, contextmanager
from typing import List
from unittest.mock import AsyncMock
import pytest
from app.auto_spatial_advisory.run_type import RunType
from datetime import datetime, timezone, timedelta
from pytest_mock import MockerFixture
from app.geospatial.wps_dataset import WPSDataset
from app.sfms.daily_ffmc_processor import DailyFFMCProcessor
from app.sfms.raster_addresser import RasterKeyAddresser, WeatherParameter
from app.tests.dataset_common import create_mock_gdal_dataset, create_mock_wps_dataset
from app.utils.geospatial import GDALResamplingMethod
from app.utils.s3_client import S3Client

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)
EXPECTED_FIRST_DAY = TEST_DATETIME - timedelta(days=1)
EXPECTED_SECOND_DAY = TEST_DATETIME


def create_mock_wps_datasets(num: int) -> List[WPSDataset]:
    return [create_mock_wps_dataset() for _ in range(num)]


def create_mock_input_dataset_context():
    input_datasets = create_mock_wps_datasets(5)

    @contextmanager
    def mock_input_dataset_context(_: List[str]):
        try:
            # Enter each dataset's context and yield the list of instances
            with ExitStack() as stack:
                yield [stack.enter_context(ds) for ds in input_datasets]
        finally:
            # Close all datasets to ensure cleanup
            for ds in input_datasets:
                ds.close()

    return input_datasets, mock_input_dataset_context


@pytest.mark.anyio
async def test_daily_ffmc_processor(mocker: MockerFixture):
    mock_key_addresser = RasterKeyAddresser()
    # key address spies
    get_daily_ffmc_key_spy = mocker.spy(mock_key_addresser, "get_daily_ffmc")
    get_daily_model_data_key_spy = mocker.spy(mock_key_addresser, "get_daily_model_data_key")
    ffmc_processor = DailyFFMCProcessor(TEST_DATETIME, mock_key_addresser)

    # mock weather parameters used for calculations
    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context()
    mock_yesterday_ffmc_ds, mock_temp_forecast_ds, mock_rh_forecast_ds, mock_precip_forecast_ds, mock_wind_speed_forecast_ds = input_datasets
    temp_ds_spy = mocker.spy(mock_temp_forecast_ds, "warp_to_match")
    rh_ds_spy = mocker.spy(mock_rh_forecast_ds, "warp_to_match")
    precip_ds_spy = mocker.spy(mock_precip_forecast_ds, "warp_to_match")
    wind_speed_ds_spy = mocker.spy(mock_wind_speed_forecast_ds, "warp_to_match")

    # mock gdal open
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())

    calculate_ffmc_spy = mocker.patch("app.sfms.daily_ffmc_processor.calculate_ffmc", return_value=([], -1))

    async with S3Client() as mock_s3_client:
        # mock s3 client
        mock_all_objects_exist = AsyncMock(return_value=True)
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data", return_value="test_key.tif")

        await ffmc_processor.process_daily_ffmc(mock_s3_client, mock_input_dataset_context)

        # Verify ffmc keys are checked for both days
        assert mock_all_objects_exist.call_count == 4

        # Verify the arguments for each call for get_weather_data_keys
        assert get_daily_ffmc_key_spy.call_args_list == [
            mocker.call(EXPECTED_FIRST_DAY, RunType.ACTUAL),
            mocker.call(EXPECTED_SECOND_DAY, RunType.ACTUAL),
        ]

        # Verify the arguments for each call for get_daily_model_data_key
        assert get_daily_model_data_key_spy.call_args_list == [
            # first day weather models
            mocker.call(TEST_DATETIME, RunType.FORECAST, WeatherParameter.TEMP),
            mocker.call(TEST_DATETIME, RunType.FORECAST, WeatherParameter.RH),
            mocker.call(TEST_DATETIME, RunType.FORECAST, WeatherParameter.PRECIP),
            mocker.call(TEST_DATETIME, RunType.FORECAST, WeatherParameter.WIND_SPEED),
            # second day
            mocker.call(TEST_DATETIME + timedelta(days=1), RunType.FORECAST, WeatherParameter.TEMP),
            mocker.call(TEST_DATETIME + timedelta(days=1), RunType.FORECAST, WeatherParameter.RH),
            mocker.call(TEST_DATETIME + timedelta(days=1), RunType.FORECAST, WeatherParameter.PRECIP),
            mocker.call(TEST_DATETIME + timedelta(days=1), RunType.FORECAST, WeatherParameter.WIND_SPEED),
        ]

        # Verify weather inputs are warped to match dmc raster, for first and second day
        assert temp_ds_spy.call_args_list == [
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert rh_ds_spy.call_args_list == [
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert precip_ds_spy.call_args_list == [
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert wind_speed_ds_spy.call_args_list == [
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_yesterday_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        for ffmc_calls in calculate_ffmc_spy.call_args_list:
            ffmc_ds = ffmc_calls[0][0]
            assert ffmc_ds == mock_yesterday_ffmc_ds
            wps_datasets = ffmc_calls[0][1:4]  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        # first and second day are persisted
        assert persist_raster_spy.call_count == 2


@pytest.mark.anyio
async def test_no_ffmc_keys_exist(mocker: MockerFixture):
    mock_s3_client = S3Client()

    mocker.patch.object(mock_s3_client, "all_objects_exist", return_value=False)

    _, mock_input_dataset_context = create_mock_input_dataset_context()

    # calculation spies
    calculate_ffmc_spy = mocker.patch("app.sfms.daily_ffmc_processor.calculate_ffmc", return_value=([], -1))

    bui_date_range_processor = DailyFFMCProcessor(TEST_DATETIME, RasterKeyAddresser())

    await bui_date_range_processor.process_daily_ffmc(mock_s3_client, mock_input_dataset_context)

    calculate_ffmc_spy.assert_not_called()
