from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIInputs, FWIParameter
from wps_shared.tests.geospatial.dataset_common import (
    create_mock_gdal_dataset,
    create_mock_input_dataset_context,
)
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi import FWIProcessor

TEST_DATETIME = datetime(2024, 10, 10, 20, tzinfo=timezone.utc)


def make_fwi_inputs(fwi_param: FWIParameter, run_type: RunType = RunType.ACTUAL) -> FWIInputs:
    param = fwi_param.value
    date_str = "20241010"
    date_iso = "2024-10-10"
    prev_date_str = "20241009"
    prev_date_iso = "2024-10-09"
    s3_prefix = "/vsis3/test-bucket"
    output_key = f"sfms/calculated/{run_type.value}/{date_iso}/{param}{date_str}.tif"
    return FWIInputs(
        temp_key=f"{s3_prefix}/sfms/interpolated/temp/2024/10/10/temp_{date_str}.tif",
        rh_key=f"{s3_prefix}/sfms/interpolated/rh/2024/10/10/rh_{date_str}.tif",
        precip_key=f"{s3_prefix}/sfms/interpolated/precip/2024/10/10/precip_{date_str}.tif",
        prev_fwi_key=f"{s3_prefix}/sfms/uploads/actual/{prev_date_iso}/{param}{prev_date_str}.tif",
        output_key=output_key,
        cog_key=f"{s3_prefix}/{output_key.removesuffix('.tif')}_cog.tif",
        run_type=run_type,
    )


@pytest.mark.anyio
async def test_fwi_processor_ffmc(mocker: MockerFixture):
    """Test that calculate_ffmc loads correct inputs and produces output."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

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

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context, fwi_inputs)

        # Verify weather + FWI keys were checked
        assert mock_all_objects_exist.call_count == 2

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

        # Verify output was persisted with the correct key
        assert persist_raster_spy.call_count == 1
        assert persist_raster_spy.call_args[0][1] == fwi_inputs.output_key

        # Verify COG was generated with the correct key
        assert generate_and_store_cog_spy.call_count == 1
        generate_and_store_cog_spy.assert_called_once_with(
            src_ds=mocker.ANY, output_path=fwi_inputs.cog_key
        )


@pytest.mark.anyio
async def test_fwi_processor_dmc(mocker: MockerFixture):
    """Test that calculate_dmc produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_dmc(mock_s3_client, mock_input_dataset_context, fwi_inputs)

        assert persist_raster_spy.call_count == 1
        assert persist_raster_spy.call_args[0][1] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_dc(mocker: MockerFixture):
    """Test that calculate_dc produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_dc(mock_s3_client, mock_input_dataset_context, fwi_inputs)

        assert persist_raster_spy.call_count == 1
        assert persist_raster_spy.call_args[0][1] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_missing_weather_keys(mocker: MockerFixture):
    """Test that processor bails when weather keys are missing."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(
            mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=False)
        )
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data")

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context, fwi_inputs)

        persist_raster_spy.assert_not_called()


@pytest.mark.anyio
async def test_fwi_processor_missing_fwi_keys(mocker: MockerFixture):
    """Test that processor bails when the previous day's FWI key is missing."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(
            mock_s3_client, "all_objects_exist", new=AsyncMock(side_effect=[True, False])
        )
        persist_raster_spy = mocker.patch.object(mock_s3_client, "persist_raster_data")

        await processor.calculate_dmc(mock_s3_client, mock_input_dataset_context, fwi_inputs)

        persist_raster_spy.assert_not_called()


@pytest.mark.anyio
async def test_fwi_processor_run_type_in_output_key(mocker: MockerFixture):
    """Test that the run_type from FWIInputs ends up in the output key."""
    processor = FWIProcessor(TEST_DATETIME)
    actual_inputs = make_fwi_inputs(FWIParameter.FFMC, run_type=RunType.ACTUAL)
    forecast_inputs = make_fwi_inputs(FWIParameter.FFMC, run_type=RunType.FORECAST)

    assert "actual" in actual_inputs.output_key
    assert "forecast" not in actual_inputs.output_key

    assert "forecast" in forecast_inputs.output_key
    assert "actual" not in forecast_inputs.output_key

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())
    mocker.patch("wps_sfms.processors.fwi.generate_and_store_cog")

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        persist_raster_spy = mocker.patch.object(
            mock_s3_client, "persist_raster_data", return_value="test_key.tif"
        )

        await processor.calculate_ffmc(mock_s3_client, mock_input_dataset_context, actual_inputs)

        output_key = persist_raster_spy.call_args[0][1]
        assert "actual" in output_key
        assert "forecast" not in output_key
