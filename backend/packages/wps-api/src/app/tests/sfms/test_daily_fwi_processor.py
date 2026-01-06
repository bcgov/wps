from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from wps_shared.geospatial.wps_dataset import WPSDataset
from app.sfms import daily_fwi_processor
from app.sfms.daily_fwi_processor import DailyFWIProcessor
from wps_shared.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from wps_shared.tests.geospatial.dataset_common import create_mock_gdal_dataset, create_mock_input_dataset_context, create_mock_new_ds_context
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.utils.s3_client import S3Client

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)
EXPECTED_FIRST_DAY = TEST_DATETIME.replace(hour=20, minute=0, second=0, microsecond=0)
EXPECTED_SECOND_DAY = TEST_DATETIME.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)


@pytest.mark.anyio
async def test_daily_fwi_processor(mocker: MockerFixture):
    mock_key_addresser = RasterKeyAddresser()
    # key address spies
    get_weather_data_key_spy = mocker.spy(mock_key_addresser, "get_weather_data_keys")
    gdal_prefix_keys_spy = mocker.spy(mock_key_addresser, "gdal_prefix_keys")
    get_calculated_index_key_spy = mocker.spy(mock_key_addresser, "get_calculated_index_key")
    get_cog_key_spy = mocker.spy(mock_key_addresser, "get_cog_key")

    fwi_processor = DailyFWIProcessor(TEST_DATETIME, 2, mock_key_addresser)

    # mock weather index, param datasets used for calculations
    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(7)
    mock_temp_ds, mock_rh_ds, mock_precip_ds, mock_wind_speed_ds, mock_dc_ds, mock_dmc_ds, mock_ffmc_ds = input_datasets
    temp_ds_spy = mocker.spy(mock_temp_ds, "warp_to_match")
    rh_ds_spy = mocker.spy(mock_rh_ds, "warp_to_match")
    wind_speed_ds_spy = mocker.spy(mock_wind_speed_ds, "warp_to_match")
    precip_ds_spy = mocker.spy(mock_precip_ds, "warp_to_match")

    # mock new dmc and dc datasets
    new_datasets, mock_new_dmc_dc_datasets_context = create_mock_new_ds_context(2)
    mock_new_dmc_ds, mock_new_dc_ds = new_datasets

    # mock new ffmc dataset
    new_datasets, mock_new_ffmc_datasets_context = create_mock_new_ds_context(1)
    mock_new_ffmc_ds = new_datasets[0]

    # mock the isi and bui datasets
    new_datasets, mock_new_isi_bui_datasets_context = create_mock_new_ds_context(2)
    mock_new_isi_ds, mock_new_bui_ds = new_datasets

    # mock gdal open
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())

    # mock warp_to_cog - patch where it's used, not where it's defined
    warp_to_cog_spy = mocker.patch("app.sfms.daily_fwi_processor.warp_to_cog")

    # calculation spies
    calculate_dmc_spy = mocker.spy(daily_fwi_processor, "calculate_dmc")
    calculate_dc_spy = mocker.spy(daily_fwi_processor, "calculate_dc")
    calculate_bui_spy = mocker.spy(daily_fwi_processor, "calculate_bui")
    calculate_ffmc_spy = mocker.spy(daily_fwi_processor, "calculate_ffmc")
    calculate_isi_spy = mocker.spy(daily_fwi_processor, "calculate_isi")
    calculate_fwi_spy = mocker.spy(daily_fwi_processor, "calculate_fwi")

    async with S3Client() as mock_s3_client:
        # mock s3 client
        mock_all_objects_exist = AsyncMock(return_value=True)
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data", return_value="test_key.tif")

        await fwi_processor.process(mock_s3_client, mock_input_dataset_context, mock_new_dmc_dc_datasets_context, mock_new_ffmc_datasets_context, mock_new_isi_bui_datasets_context, mock_new_ffmc_datasets_context)

        # Verify weather model keys and actual keys are checked for both days
        assert mock_all_objects_exist.call_count == 4

        # Verify the arguments for each call for get_weather_data_keys
        assert get_weather_data_key_spy.call_args_list == [
            mocker.call(TEST_DATETIME, EXPECTED_FIRST_DAY, 20),
            mocker.call(TEST_DATETIME, EXPECTED_SECOND_DAY, 44),
        ]

        # Verify the arguments for each call for gdal_prefix_keys
        assert gdal_prefix_keys_spy.call_args_list == [
            # first day weather models
            mocker.call(
                "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P020.grib2",
                "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P020.grib2",
                "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P020.grib2",
                "weather_models/rdps/2024-10-10/12/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_20z.tif",
                "sfms/uploads/actual/2024-10-09/ffmc20241009.tif",
            ),
            # first day uploads
            mocker.call("sfms/uploads/actual/2024-10-09/dc20241009.tif", "sfms/uploads/actual/2024-10-09/dmc20241009.tif"),
            # second day weather models
            mocker.call(
                "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P044.grib2",
                "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P044.grib2",
                "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P044.grib2",
                "weather_models/rdps/2024-10-11/12/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241011_20z.tif",
                "sfms/calculated/forecast/2024-10-10/ffmc20241010.tif",
            ),
            # second day uploads
            mocker.call("sfms/calculated/forecast/2024-10-10/dc20241010.tif", "sfms/calculated/forecast/2024-10-10/dmc20241010.tif"),
        ]

        # Verify calculated keys are generated in order
        assert get_calculated_index_key_spy.call_args_list == [
            # first day
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.DMC),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.DC),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.FFMC),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.BUI),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.ISI),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.FWI),
            # second day, previous days' dc and dmc are looked up first
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.DC),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.DMC),
            mocker.call(EXPECTED_FIRST_DAY, FWIParameter.FFMC),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.DMC),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.DC),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.FFMC),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.BUI),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.ISI),
            mocker.call(EXPECTED_SECOND_DAY, FWIParameter.FWI),
        ]

        # Verify weather inputs are warped to match dmc raster
        assert temp_ds_spy.call_args_list == [
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert rh_ds_spy.call_args_list == [
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR, max_value=100),
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR, max_value=100),
        ]

        assert wind_speed_ds_spy.call_args_list == [
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        assert precip_ds_spy.call_args_list == [
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
            mocker.call(mock_dmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR),
        ]

        for dmc_calls in calculate_dmc_spy.call_args_list:
            dmc_ds = dmc_calls.args[0]
            assert dmc_ds == mock_dmc_ds
            wps_datasets = dmc_calls[0][1:4]  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        for dc_calls in calculate_dc_spy.call_args_list:
            dc_ds = dc_calls.args[0]
            assert dc_ds == mock_dc_ds
            wps_datasets = dc_calls[0][1:4]  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        for ffmc_calls in calculate_ffmc_spy.call_args_list:
            ffmc_ds = ffmc_calls.args[0]
            assert ffmc_ds == mock_ffmc_ds
            wps_datasets = ffmc_calls[0][1:4]  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        assert calculate_bui_spy.call_args_list == [
            mocker.call(mock_new_dmc_ds, mock_new_dc_ds),
            mocker.call(mock_new_dmc_ds, mock_new_dc_ds),
        ]

        for isi_calls in calculate_isi_spy.call_args_list:
            ffmc_ds = isi_calls.args[0]
            assert ffmc_ds == mock_new_ffmc_ds
            wps_datasets = isi_calls.args  # Extract dataset arguments
            assert all(isinstance(ds, WPSDataset) for ds in wps_datasets)

        assert calculate_fwi_spy.call_args_list == [
            mocker.call(mock_new_isi_ds, mock_new_bui_ds),
            mocker.call(mock_new_isi_ds, mock_new_bui_ds),
        ]

        # 6 each day, new dmc, dc, ffmc, bui, isi, and fwi rasters
        assert persist_raster_spy.call_count == 12

        # 6 COG conversions per day (dmc, dc, ffmc, bui, isi, fwi)
        assert warp_to_cog_spy.call_count == 12

        # 6 COG keys generated per day (dmc, dc, ffmc, bui, isi, fwi)
        assert get_cog_key_spy.call_count == 12

        # Verify get_cog_key is called with the correct keys
        assert get_cog_key_spy.call_args_list == [
            # first day
            mocker.call("sfms/calculated/forecast/2024-10-10/dmc20241010.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-10/dc20241010.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-10/ffmc20241010.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-10/bui20241010.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-10/isi20241010.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-10/fwi20241010.tif"),
            # second day
            mocker.call("sfms/calculated/forecast/2024-10-11/dmc20241011.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-11/dc20241011.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-11/ffmc20241011.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-11/bui20241011.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-11/isi20241011.tif"),
            mocker.call("sfms/calculated/forecast/2024-10-11/fwi20241011.tif"),
        ]


@pytest.mark.parametrize(
    "side_effect_1, side_effect_2",
    [
        (False, False),
        (True, False),
        (False, True),
    ],
)
@pytest.mark.anyio
async def test_no_weather_keys_exist(side_effect_1: bool, side_effect_2: bool, mocker: MockerFixture):
    mock_s3_client = S3Client()

    mocker.patch.object(mock_s3_client, "all_objects_exist", side_effect=[side_effect_1, side_effect_2])

    _, mock_input_dataset_context = create_mock_input_dataset_context(7)

    _, mock_new_dmc_dc_datasets_context = create_mock_new_ds_context(2)
    _, mock_new_ffmc_dataset_context = create_mock_new_ds_context(1)
    _, mock_new_isi_bui_datasets_context = create_mock_new_ds_context(2)

    # calculation spies
    calculate_dmc_spy = mocker.spy(daily_fwi_processor, "calculate_dmc")
    calculate_dc_spy = mocker.spy(daily_fwi_processor, "calculate_dc")
    calculate_bui_spy = mocker.spy(daily_fwi_processor, "calculate_bui")
    calculate_ffmc_spy = mocker.spy(daily_fwi_processor, "calculate_ffmc")
    calculate_isi_spy = mocker.spy(daily_fwi_processor, "calculate_isi")
    calculate_fwi_spy = mocker.spy(daily_fwi_processor, "calculate_fwi")

    fwi_processor = DailyFWIProcessor(TEST_DATETIME, 1, RasterKeyAddresser())

    await fwi_processor.process(mock_s3_client, mock_input_dataset_context, mock_new_dmc_dc_datasets_context, mock_new_ffmc_dataset_context, mock_new_isi_bui_datasets_context, mock_new_ffmc_dataset_context)

    calculate_dmc_spy.assert_not_called()
    calculate_dc_spy.assert_not_called()
    calculate_bui_spy.assert_not_called()
    calculate_ffmc_spy.assert_not_called()
    calculate_isi_spy.assert_not_called()
    calculate_fwi_spy.assert_not_called()
