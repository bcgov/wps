from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from wps_shared.geospatial.wps_dataset import WPSDataset
from app.sfms import hourly_ffmc_processor
from app.sfms.hourly_ffmc_processor import HourlyFFMCProcessor
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.tests.geospatial.dataset_common import create_mock_gdal_dataset, create_mock_input_dataset_context, create_mock_new_ds_context
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.utils.s3_client import S3Client

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)
RDPS_MODEL_RUN_DATETIME = datetime(2024, 10, 10, 0, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_source_hffmc_key_not_exist(mocker: MockerFixture):
    mock_s3_client = S3Client()
    mocker.patch.object(mock_s3_client, "all_objects_exist", side_effect=[False])
    _, mock_input_dataset_context = create_mock_new_ds_context(2)

    # calculation spies
    calculate_hffmc_spy = mocker.spy(hourly_ffmc_processor, "calculate_ffmc")

    hffmc_processor = HourlyFFMCProcessor(TEST_DATETIME, RasterKeyAddresser())
    await hffmc_processor.process(mock_s3_client, mock_input_dataset_context)

    calculate_hffmc_spy.assert_not_called()


@pytest.mark.anyio
async def test_no_weather_keys_exist(mocker: MockerFixture):
    mock_s3_client = S3Client()
    mocker.patch.object(mock_s3_client, "all_objects_exist", side_effect=[True, False])
    _, mock_input_dataset_context = create_mock_new_ds_context(2)

    # calculation spy
    calculate_hffmc_spy = mocker.spy(hourly_ffmc_processor, "calculate_ffmc")

    hffmc_processor = HourlyFFMCProcessor(TEST_DATETIME, RasterKeyAddresser())
    await hffmc_processor.process(mock_s3_client, mock_input_dataset_context)

    calculate_hffmc_spy.assert_not_called()


@pytest.mark.anyio
async def test_hourly_ffmc_processor(mocker: MockerFixture):
    num_hours_to_process = 2
    mock_key_addresser = RasterKeyAddresser()
    # key address spies
    get_weather_data_keys_hffmc_spy = mocker.spy(mock_key_addresser, "get_weather_data_keys_hffmc")
    gdal_prefix_keys_spy = mocker.spy(mock_key_addresser, "gdal_prefix_keys")
    get_uploaded_hffmc_key_spy = mocker.spy(mock_key_addresser, "get_uploaded_hffmc_key")
    get_calculated_hffmc_index_key_spy = mocker.spy(mock_key_addresser, "get_calculated_hffmc_index_key")

    # The processor instance
    hffmc_processor = HourlyFFMCProcessor(TEST_DATETIME, mock_key_addresser)

    # mock weather index and source hffmc dataset used for calculations
    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(5)
    mock_temp_ds, mock_rh_ds, mock_precip_ds, mock_wind_speed_ds, mock_hffmc_ds = input_datasets

    # dataset spies
    temp_ds_spy = mocker.spy(mock_temp_ds, "warp_to_match")
    rh_ds_spy = mocker.spy(mock_rh_ds, "warp_to_match")
    wind_speed_ds_spy = mocker.spy(mock_wind_speed_ds, "warp_to_match")
    precip_ds_spy = mocker.spy(mock_precip_ds, "warp_to_match")

    # mock gdal open
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())

    # calculation spy
    calculate_hffmc_spy = mocker.spy(hourly_ffmc_processor, "calculate_ffmc")

    async with S3Client() as mock_s3_client:
        # mock s3 client
        mock_all_objects_exist = AsyncMock(return_value=True)
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data", return_value="test_key.tif")

        await hffmc_processor.process(mock_s3_client, mock_input_dataset_context, num_hours_to_process)

        # Verify weather model keys and actual keys are checked for both days
        assert mock_all_objects_exist.call_count == num_hours_to_process + 1

        # Verify retrivel of hffmc
        assert get_uploaded_hffmc_key_spy.call_args_list == [mocker.call(RDPS_MODEL_RUN_DATETIME)]

        # Verify the arguments for each call for get_weather_data_keys
        assert get_weather_data_keys_hffmc_spy.call_args_list == [
            mocker.call(RDPS_MODEL_RUN_DATETIME, 0),
            mocker.call(RDPS_MODEL_RUN_DATETIME, 1),
        ]

        # Verify the arguments for each call for gdal_prefix_keys
        assert gdal_prefix_keys_spy.call_args_list == [
            # first hour weather models and source hffmc
            mocker.call(
                "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P000.grib2",
                "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P000.grib2",
                "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P000.grib2",
                "weather_models/rdps/2024-10-10/00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_00z.tif",
                "sfms/uploads/hourlies/2024-10-09/fine_fuel_moisture_code2024100916.tif",
            ),
            mocker.call(
                "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P001.grib2",
                "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P001.grib2",
                "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P001.grib2",
                "weather_models/rdps/2024-10-10/00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_01z.tif",
                "sfms/calculated/hourlies/2024-10-10/fine_fuel_moisture_code2024101000.tif",
            ),
        ]

        # Verify calculated keys are generated in order
        assert get_calculated_hffmc_index_key_spy.call_args_list == [
            # first day
            mocker.call(RDPS_MODEL_RUN_DATETIME + timedelta(hours=0)),
            mocker.call(RDPS_MODEL_RUN_DATETIME + timedelta(hours=1)),
        ]

        # Verify weather inputs are warped to match source hffmc raster
        assert temp_ds_spy.call_args_list == [
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert rh_ds_spy.call_args_list == [
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR, max_value=100),
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR, max_value=100),
        ]

        assert wind_speed_ds_spy.call_args_list == [
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert precip_ds_spy.call_args_list == [
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_hffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        for hffmc_calls in calculate_hffmc_spy.call_args_list:
            hffmc_ds = hffmc_calls.args[0]
            assert hffmc_ds == mock_hffmc_ds
            wps_datasets = hffmc_calls[0]  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        # 1 hffmc per day
        assert persist_raster_spy.call_count == 2
