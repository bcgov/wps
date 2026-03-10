from datetime import datetime, timezone
from unittest.mock import AsyncMock

import numpy as np
import pytest
from pytest_mock import MockerFixture

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_sfms.sfmsng_raster_addresser import FWIInputs
from wps_shared.tests.geospatial.dataset_common import (
    create_mock_input_dataset_context,
    create_test_dataset,
)
from wps_shared.utils.s3_client import S3Client
from wps_sfms.processors.fwi import (
    BUICalculator,
    DCCalculator,
    DMCCalculator,
    FFMCCalculator,
    FWICalculator,
    FWIDatasets,
    FWIFinalCalculator,
    FWIProcessor,
    ISICalculator,
)

TEST_DATETIME = datetime(2024, 10, 10, 20, tzinfo=timezone.utc)


@pytest.mark.parametrize("month", range(1, 13))
def test_monthly_fwi_calculator_valid_months(month):
    DMCCalculator(month)  # should not raise


@pytest.mark.parametrize("month", [0, 13, -1])
def test_monthly_fwi_calculator_invalid_month_raises(month):
    with pytest.raises(ValueError, match="month must be"):
        DMCCalculator(month)


def make_fwi_inputs(fwi_param: FWIParameter, run_type: RunType = RunType.ACTUAL) -> FWIInputs:
    param = fwi_param.value
    date_str = "20241010"
    date_iso = "2024-10-10"
    prev_date_str = "20241009"
    prev_date_iso = "2024-10-09"
    s3_prefix = "/vsis3/test-bucket"
    output_key = f"sfms/calculated/{run_type.value}/{date_iso}/{param}{date_str}.tif"

    weather_keys = {
        SFMSInterpolatedWeatherParameter.TEMP: f"{s3_prefix}/sfms/interpolated/temp/2024/10/10/temp_{date_str}.tif",
        SFMSInterpolatedWeatherParameter.RH: f"{s3_prefix}/sfms/interpolated/rh/2024/10/10/rh_{date_str}.tif",
        SFMSInterpolatedWeatherParameter.PRECIP: f"{s3_prefix}/sfms/interpolated/precip/2024/10/10/precip_{date_str}.tif",
        SFMSInterpolatedWeatherParameter.WIND_SPEED: f"{s3_prefix}/sfms/interpolated/wind_speed/2024/10/10/wind_speed_{date_str}.tif",
    }

    if fwi_param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC):
        index_keys = {
            fwi_param: f"{s3_prefix}/sfms/uploads/actual/{prev_date_iso}/{param}{prev_date_str}.tif"
        }
    elif fwi_param == FWIParameter.ISI:
        index_keys = {
            FWIParameter.FFMC: f"{s3_prefix}/sfms/calculated/actual/{date_iso}/ffmc{date_str}.tif"
        }
    elif fwi_param == FWIParameter.BUI:
        index_keys = {
            FWIParameter.DMC: f"{s3_prefix}/sfms/calculated/actual/{date_iso}/dmc{date_str}.tif",
            FWIParameter.DC: f"{s3_prefix}/sfms/calculated/actual/{date_iso}/dc{date_str}.tif",
        }
    elif fwi_param == FWIParameter.FWI:
        index_keys = {
            FWIParameter.ISI: f"{s3_prefix}/sfms/calculated/actual/{date_iso}/isi{date_str}.tif",
            FWIParameter.BUI: f"{s3_prefix}/sfms/calculated/actual/{date_iso}/bui{date_str}.tif",
        }
    else:
        raise AssertionError(f"Unhandled FWI parameter for test: {fwi_param}")

    return FWIInputs(
        weather_keys=weather_keys,
        index_keys=index_keys,
        output_key=output_key,
        run_type=run_type,
    )


@pytest.mark.anyio
async def test_fwi_processor_ffmc(mocker: MockerFixture):
    """Test that calculate_index with FFMCCalculator loads correct inputs and produces output."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(5)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )
    rasters_match_spy = mocker.patch("wps_sfms.processors.fwi.rasters_match", return_value=True)

    async with S3Client() as mock_s3_client:
        mock_all_objects_exist = AsyncMock(return_value=True)
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)

        await processor.calculate_index(
            mock_s3_client, mock_input_dataset_context, FFMCCalculator(), fwi_inputs
        )

        # Verify weather + FWI keys were checked
        assert mock_all_objects_exist.call_count == 2

        # Verify all required weather rasters were checked against the FWI grid
        assert rasters_match_spy.call_count == 4

        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_dmc(mocker: MockerFixture):
    """Test that calculate_index with DMCCalculator produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client,
            mock_input_dataset_context,
            DMCCalculator(TEST_DATETIME.month),
            fwi_inputs,
        )

        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_dc(mocker: MockerFixture):
    """Test that calculate_index with DCCalculator produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client,
            mock_input_dataset_context,
            DCCalculator(TEST_DATETIME.month),
            fwi_inputs,
        )

        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_missing_weather_keys(mocker: MockerFixture):
    """Test that processor bails when weather keys are missing."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=False))
        publish_spy = mocker.patch(
            "wps_sfms.processors.fwi.publish_dataset",
            new=AsyncMock(),
        )

        with pytest.raises(RuntimeError, match="Missing weather dependency keys"):
            await processor.calculate_index(
                mock_s3_client, mock_input_dataset_context, FFMCCalculator(), fwi_inputs
            )

        publish_spy.assert_not_called()


@pytest.mark.anyio
async def test_fwi_processor_missing_fwi_keys(mocker: MockerFixture):
    """Test that processor bails when required index dependency keys are missing."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.DMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(4)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(
            mock_s3_client, "all_objects_exist", new=AsyncMock(side_effect=[True, False])
        )
        publish_spy = mocker.patch(
            "wps_sfms.processors.fwi.publish_dataset",
            new=AsyncMock(),
        )

        with pytest.raises(RuntimeError, match="Missing index dependency keys"):
            await processor.calculate_index(
                mock_s3_client,
                mock_input_dataset_context,
                DMCCalculator(TEST_DATETIME.month),
                fwi_inputs,
            )

        publish_spy.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "match_side_effects,expected_message",
    [
        ([False], "temperature raster does not match FWI grid"),
        ([True, False], "relative_humidity raster does not match FWI grid"),
        ([True, True, False], "precipitation raster does not match FWI grid"),
        ([True, True, True, False], "wind_speed raster does not match FWI grid"),
    ],
    ids=["temp_mismatch", "rh_mismatch", "precip_mismatch", "wind_mismatch"],
)
async def test_fwi_processor_raster_mismatch_raises(
    mocker: MockerFixture, match_side_effects, expected_message
):
    """Test that ValueError is raised when any weather raster does not match the FWI grid."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(5)
    mocker.patch("wps_sfms.processors.fwi.rasters_match", side_effect=match_side_effects)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))
        publish_spy = mocker.patch(
            "wps_sfms.processors.fwi.publish_dataset",
            new=AsyncMock(),
        )

        with pytest.raises(ValueError, match=expected_message):
            await processor.calculate_index(
                mock_s3_client, mock_input_dataset_context, FFMCCalculator(), fwi_inputs
            )

        publish_spy.assert_not_called()


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

    _, mock_input_dataset_context = create_mock_input_dataset_context(5)
    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client, mock_input_dataset_context, FFMCCalculator(), actual_inputs
        )

        output_key = publish_spy.await_args.kwargs["output_key"]
        assert "actual" in output_key
        assert "forecast" not in output_key


@pytest.mark.anyio
async def test_fwi_processor_isi(mocker: MockerFixture):
    """Test that calculate_index with ISICalculator produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.ISI)

    _, mock_input_dataset_context = create_mock_input_dataset_context(2)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )
    rasters_match_spy = mocker.patch("wps_sfms.processors.fwi.rasters_match", return_value=True)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client,
            mock_input_dataset_context,
            ISICalculator(),
            fwi_inputs,
        )

        assert rasters_match_spy.call_count == 1
        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_bui(mocker: MockerFixture):
    """Test that calculate_index with BUICalculator produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.BUI)

    _, mock_input_dataset_context = create_mock_input_dataset_context(2)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )
    rasters_match_spy = mocker.patch("wps_sfms.processors.fwi.rasters_match", return_value=True)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client,
            mock_input_dataset_context,
            BUICalculator(),
            fwi_inputs,
        )

        assert rasters_match_spy.call_count == 1
        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_fwi(mocker: MockerFixture):
    """Test that calculate_index with FWIFinalCalculator produces output with correct key."""
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FWI)

    _, mock_input_dataset_context = create_mock_input_dataset_context(2)

    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        new=AsyncMock(),
    )
    rasters_match_spy = mocker.patch("wps_sfms.processors.fwi.rasters_match", return_value=True)

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        await processor.calculate_index(
            mock_s3_client,
            mock_input_dataset_context,
            FWIFinalCalculator(),
            fwi_inputs,
        )

        assert rasters_match_spy.call_count == 1
        assert publish_spy.call_count == 1
        assert publish_spy.await_args.kwargs["output_key"] == fwi_inputs.output_key


@pytest.mark.anyio
async def test_fwi_processor_cog_failure_propagates(mocker: MockerFixture):
    """If COG generation fails after a successful persist, the error propagates.

    This covers the partial-success scenario where the raster is written to S3
    but the COG is not — the caller must see the failure so it can be retried.
    """
    processor = FWIProcessor(TEST_DATETIME)
    fwi_inputs = make_fwi_inputs(FWIParameter.FFMC)

    _, mock_input_dataset_context = create_mock_input_dataset_context(5)
    mocker.patch("wps_sfms.processors.fwi.rasters_match", return_value=True)
    publish_spy = mocker.patch(
        "wps_sfms.processors.fwi.publish_dataset",
        side_effect=RuntimeError("COG generation failed"),
    )

    async with S3Client() as mock_s3_client:
        mocker.patch.object(mock_s3_client, "all_objects_exist", new=AsyncMock(return_value=True))

        with pytest.raises(RuntimeError, match="COG generation failed"):
            await processor.calculate_index(
                mock_s3_client, mock_input_dataset_context, FFMCCalculator(), fwi_inputs
            )

        publish_spy.assert_called_once()


class TestFWINodeataPropagation:
    """Nodata in any input raster must propagate as nodata in the output."""

    NODATA = -9999.0
    # 2x2 WGS84 grid over southern BC (lat ~48–50, lon ~-121–-119)
    EXTENT = (-121.0, -119.0, 48.0, 50.0)

    def make_ds(self, fill: float, nodata_at: tuple | None = None) -> WPSDataset:
        """2x2 dataset filled with *fill*; optionally set one pixel to NODATA."""
        gdal_ds = create_test_dataset("test.tif", 2, 2, self.EXTENT, 4326, no_data_value=self.NODATA)
        arr = np.full((2, 2), fill, dtype=np.float32)
        if nodata_at is not None:
            arr[nodata_at] = self.NODATA
        gdal_ds.GetRasterBand(1).WriteArray(arr)
        return WPSDataset(ds_path=None, ds=gdal_ds)

    @pytest.mark.parametrize(
        "calculator,prev_value",
        [
            (FFMCCalculator(), 85.0),
            (DMCCalculator(6), 20.0),
            (DCCalculator(6), 200.0),
        ],
        ids=["ffmc", "dmc", "dc"],
    )
    @pytest.mark.parametrize(
        "nodata_input",
        ["prev_fwi", "temp", "rh", "precip"],
    )
    def test_nodata_propagates(self, calculator: FWICalculator, prev_value, nodata_input):
        nodata_pixel = (0, 0)
        prev_ds = self.make_ds(prev_value, nodata_at=nodata_pixel if nodata_input == "prev_fwi" else None)
        temp_ds = self.make_ds(20.0, nodata_at=nodata_pixel if nodata_input == "temp" else None)
        rh_ds = self.make_ds(50.0, nodata_at=nodata_pixel if nodata_input == "rh" else None)
        precip_ds = self.make_ds(0.0, nodata_at=nodata_pixel if nodata_input == "precip" else None)

        wind_ds = self.make_ds(10.0)
        weather_datasets = {
            SFMSInterpolatedWeatherParameter.TEMP: temp_ds,
            SFMSInterpolatedWeatherParameter.RH: rh_ds,
            SFMSInterpolatedWeatherParameter.PRECIP: precip_ds,
            SFMSInterpolatedWeatherParameter.WIND_SPEED: wind_ds,
        }
        index_datasets = {calculator.reference_index_param: prev_ds}

        result = calculator.calculate(
            FWIDatasets(index=index_datasets, weather=weather_datasets)
        )

        assert np.isnan(result.nodata_value)
        assert np.isnan(result.values[0, 0]), "nodata pixel must propagate as NaN"
        # All other pixels must have been computed (not NaN)
        assert not np.isnan(result.values[0, 1])
        assert not np.isnan(result.values[1, 0])
        assert not np.isnan(result.values[1, 1])
