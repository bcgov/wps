from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from wps_shared.tests.geospatial.dataset_common import (
    create_mock_gdal_dataset,
    create_mock_input_dataset_context,
)
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi import ActualFWIProcessor

TEST_DATETIME = datetime(2024, 10, 10, 20, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_actual_fwi_processor_ffmc(mocker: MockerFixture):
    """Test that calculate_ffmc loads correct inputs and produces output."""
    mock_key_addresser = RasterKeyAddresser()
    get_interpolated_key_spy = mocker.spy(mock_key_addresser, "get_interpolated_key")
    get_uploaded_index_key_spy = mocker.spy(mock_key_addresser, "get_uploaded_index_key")
    get_calculated_index_key_spy = mocker.spy(mock_key_addresser, "get_calculated_index_key")
    get_cog_key_spy = mocker.spy(mock_key_addresser, "get_cog_key")

    processor = ActualFWIProcessor(TEST_DATETIME, mock_key_addresser)

    # 4 input datasets: temp, rh, precip, prev_ffmc
    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(4)
    mock_temp_ds, mock_rh_ds, mock_precip_ds, mock_prev_ffmc_ds = input_datasets

    temp_ds_spy = mocker.spy(mock_temp_ds, "warp_to_match")
    rh_ds_spy = mocker.spy(mock_rh_ds, "warp_to_match")
    precip_ds_spy = mocker.spy(mock_precip_ds, "warp_to_match")

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    generate_and_store_cog_spy = mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mock_all_objects_exist = AsyncMock(return_value=True)
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context)

        # Verify weather + FWI keys were checked
        assert mock_all_objects_exist.call_count == 2

        # Verify interpolated keys were fetched for temp, rh, precip
        assert get_interpolated_key_spy.call_count == 3

        # Verify yesterday's FFMC was fetched
        get_uploaded_index_key_spy.assert_called_once()

        # Verify weather was warped to match prev FWI grid
        temp_ds_spy.assert_called_once_with(
            mock_prev_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR
        )
        rh_ds_spy.assert_called_once_with(
            mock_prev_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR, max_value=100
        )
        precip_ds_spy.assert_called_once_with(
            mock_prev_ffmc_ds, mocker.ANY, GDALResamplingMethod.BILINEAR
        )

        # Verify output was persisted
        assert persist_raster_spy.call_count == 1

        # Verify calculated key uses run_type="actual"
        get_calculated_index_key_spy.assert_called_once_with(
            TEST_DATETIME, FWIParameter.FFMC, run_type="actual"
        )

        # Verify COG was generated
        assert generate_and_store_cog_spy.call_count == 1
        assert get_cog_key_spy.call_count == 1


@pytest.mark.anyio
async def test_actual_fwi_processor_dmc(mocker: MockerFixture):
    """Test that calculate_dmc loads correct inputs and produces output."""
    mock_key_addresser = RasterKeyAddresser()
    get_calculated_index_key_spy = mocker.spy(mock_key_addresser, "get_calculated_index_key")

    processor = ActualFWIProcessor(TEST_DATETIME, mock_key_addresser)

    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(4)

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_dmc(mock_s3_client, mock_input_dataset_context)

        assert persist_raster_spy.call_count == 1
        get_calculated_index_key_spy.assert_called_once_with(
            TEST_DATETIME, FWIParameter.DMC, run_type="actual"
        )


@pytest.mark.anyio
async def test_actual_fwi_processor_dc(mocker: MockerFixture):
    """Test that calculate_dc loads correct inputs and produces output."""
    mock_key_addresser = RasterKeyAddresser()
    get_calculated_index_key_spy = mocker.spy(mock_key_addresser, "get_calculated_index_key")

    processor = ActualFWIProcessor(TEST_DATETIME, mock_key_addresser)

    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(4)

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_dc(mock_s3_client, mock_input_dataset_context)

        assert persist_raster_spy.call_count == 1
        get_calculated_index_key_spy.assert_called_once_with(
            TEST_DATETIME, FWIParameter.DC, run_type="actual"
        )


@pytest.mark.anyio
async def test_actual_fwi_processor_missing_weather_keys(mocker: MockerFixture):
    """Test that processor bails when weather keys are missing."""
    processor = ActualFWIProcessor(TEST_DATETIME, RasterKeyAddresser())

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        # Weather keys don't exist
        mocker.patch.object(
            mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=False)
        )
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data")

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context)

        persist_raster_spy.assert_not_called()


@pytest.mark.anyio
async def test_actual_fwi_processor_missing_fwi_keys(mocker: MockerFixture):
    """Test that processor bails when yesterday's FWI keys are missing."""
    processor = ActualFWIProcessor(TEST_DATETIME, RasterKeyAddresser())

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        # Weather keys exist, FWI keys don't
        mocker.patch.object(
            mock_s3_client, "all_objects_exist", new=AsyncMock(side_effect=[True, False])
        )
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data")

        await processor.calculate_dmc(mock_s3_client, mock_input_dataset_context)

        persist_raster_spy.assert_not_called()


@pytest.mark.anyio
async def test_actual_fwi_processor_output_keys(mocker: MockerFixture):
    """Test that output keys use the 'actual' run_type path."""
    mock_key_addresser = RasterKeyAddresser()
    processor = ActualFWIProcessor(TEST_DATETIME, mock_key_addresser)

    input_datasets, mock_input_dataset_context = create_mock_input_dataset_context(4)

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context)

        # Verify the output key contains "actual" instead of "forecast"
        persist_call_args = persist_raster_spy.call_args
        output_key = persist_call_args[0][1]  # second positional arg is the key
        assert "actual" in output_key
        assert "forecast" not in output_key
        assert "ffmc" in output_key
