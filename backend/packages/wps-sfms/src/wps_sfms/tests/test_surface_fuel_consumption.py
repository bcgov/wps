from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import cffdrs.surface_fuel_consumption
import numpy as np
import pytest
from osgeo import gdal, osr
from pytest_mock import MockerFixture
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.processors.surface_fuel_consumption import (
    SurfaceFuelConsumptionDatasets,
    SurfaceFuelConsumptionProcessor,
    calculate_surface_fuel_consumption,
)
from wps_sfms.raster_inputs import SurfaceFuelConsumptionInputs

TEST_DATETIME = datetime(2024, 7, 4, 20, tzinfo=timezone.utc)
NODATA = -9999.0


def make_dataset(path: str, values: np.ndarray, nodata: float = NODATA) -> WPSDataset:
    rows, columns = values.shape
    dataset = gdal.GetDriverByName("MEM").Create("", columns, rows, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((0, 2_000, 0, 10_000, 0, -2_000))
    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(3005)
    dataset.SetProjection(spatial_reference.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(values)
    return WPSDataset(ds_path=path, ds=dataset)


@pytest.fixture(autouse=True)
def output_mask(mocker: MockerFixture):
    mask = make_dataset("mask.tif", np.ones((1, 1), dtype=np.float32))

    @contextmanager
    def mask_context():
        yield mask

    mocker.patch("wps_sfms.raster_output.open_bc_mask_dataset", side_effect=mask_context)
    yield mask
    mask.close()


def make_datasets(
    fuel: np.ndarray,
    ffmc: np.ndarray | None = None,
    bui: np.ndarray | None = None,
    percent_conifer: np.ndarray | None = None,
) -> SurfaceFuelConsumptionDatasets:
    shape = fuel.shape
    return SurfaceFuelConsumptionDatasets(
        fuel=make_dataset("fuel.tif", fuel),
        ffmc=make_dataset("ffmc.tif", ffmc if ffmc is not None else np.full(shape, 90.0)),
        bui=make_dataset("bui.tif", bui if bui is not None else np.full(shape, 60.0)),
        percent_conifer=make_dataset(
            "percent_conifer.tif",
            percent_conifer if percent_conifer is not None else np.full(shape, NODATA),
        ),
    )


@pytest.mark.parametrize(
    "grid_value,fuel_type,percent_conifer",
    [
        (1, "C1", 0.0),
        (2, "C2", 0.0),
        (3, "C3", 0.0),
        (4, "C4", 0.0),
        (5, "C5", 0.0),
        (6, "C6", 0.0),
        (7, "C7", 0.0),
        (8, "D1", 0.0),
        (9, "S1", 0.0),
        (10, "S2", 0.0),
        (11, "S3", 0.0),
        (12, "O1A", 0.0),
        (13, "M3", 0.0),
        (14, "M1", 40.0),
    ],
)
def test_calculation_matches_cffdrs_reference(
    grid_value: int, fuel_type: str, percent_conifer: float
):
    datasets = make_datasets(
        np.array([[grid_value]], dtype=np.float32),
        percent_conifer=np.array([[percent_conifer]], dtype=np.float32),
    )

    result = calculate_surface_fuel_consumption(datasets)

    expected = cffdrs.surface_fuel_consumption.surface_fuel_consumption(
        fuel_type, 90.0, 60.0, percent_conifer, 0.35
    )
    assert result.values[0, 0] == pytest.approx(expected)


def test_non_fuel_becomes_zero_and_source_nodata_remains_sfms_nodata():
    fuel = np.array([[99, 102, NODATA]], dtype=np.float32)
    datasets = make_datasets(fuel)

    result = calculate_surface_fuel_consumption(datasets)

    np.testing.assert_array_equal(result.values, np.array([[0, 0, SFMS_NO_DATA]], dtype=np.float32))


def test_non_fuel_becomes_zero_when_weather_is_nodata():
    datasets = make_datasets(
        np.array([[99, 102]], dtype=np.float32),
        ffmc=np.full((1, 2), NODATA, dtype=np.float32),
        bui=np.full((1, 2), NODATA, dtype=np.float32),
    )

    result = calculate_surface_fuel_consumption(datasets)

    np.testing.assert_array_equal(result.values, np.zeros((1, 2), dtype=np.float32))


def test_weather_nodata_propagates_to_output():
    datasets = make_datasets(
        np.array([[1, 2]], dtype=np.float32),
        ffmc=np.array([[NODATA, 90]], dtype=np.float32),
        bui=np.array([[60, NODATA]], dtype=np.float32),
    )

    result = calculate_surface_fuel_consumption(datasets)

    np.testing.assert_array_equal(result.values, np.full((1, 2), SFMS_NO_DATA, dtype=np.float32))


def test_percent_conifer_nodata_is_ignored_outside_mixedwood():
    datasets = make_datasets(np.array([[1]], dtype=np.float32))

    result = calculate_surface_fuel_consumption(datasets)

    assert result.values[0, 0] != SFMS_NO_DATA


@pytest.mark.parametrize("percent_conifer", [NODATA, -1, 101])
def test_invalid_mixedwood_percent_conifer_fails(percent_conifer: float):
    datasets = make_datasets(
        np.array([[14]], dtype=np.float32),
        percent_conifer=np.array([[percent_conifer]], dtype=np.float32),
    )

    with pytest.raises(ValueError, match="missing or out-of-range"):
        calculate_surface_fuel_consumption(datasets)


def make_inputs() -> SurfaceFuelConsumptionInputs:
    return SurfaceFuelConsumptionInputs(
        fuel_key="/vsis3/test/fuel.tif",
        ffmc_key="/vsis3/test/ffmc.tif",
        bui_key="/vsis3/test/bui.tif",
        percent_conifer_key="/vsis3/test/percent_conifer.tif",
        output_key="sfms_ng/actual/2024/07/04/sfc_20240704.tif",
        run_type=RunType.ACTUAL,
    )


def make_dataset_context(datasets: SurfaceFuelConsumptionDatasets, reverse: bool = False):
    @contextmanager
    def dataset_context(keys):
        input_datasets = [
            datasets.fuel,
            datasets.ffmc,
            datasets.bui,
            datasets.percent_conifer,
        ]
        for dataset, key in zip(input_datasets, keys, strict=True):
            dataset.ds_path = key
        yield list(reversed(input_datasets)) if reverse else input_datasets

    return dataset_context


def test_processor_binds_opened_datasets_by_input_key():
    datasets = make_datasets(np.array([[1]], dtype=np.float32))
    inputs = make_inputs()
    processor = SurfaceFuelConsumptionProcessor(TEST_DATETIME)

    with processor._open_datasets(
        make_dataset_context(datasets, reverse=True), inputs
    ) as opened_datasets:
        assert opened_datasets == datasets


@pytest.mark.anyio
async def test_processor_publishes_masked_output_with_metadata(
    mocker: MockerFixture,
    output_mask: WPSDataset,
):
    datasets = make_datasets(np.array([[1]], dtype=np.float32))
    inputs = make_inputs()
    captured = {}
    output_mask.as_gdal_ds().GetRasterBand(1).WriteArray(np.array([[0]], dtype=np.float32))

    async def capture_publish(*, dataset, output_key, **_kwargs):
        band = dataset.as_gdal_ds().GetRasterBand(1)
        captured["output_key"] = output_key
        captured["description"] = band.GetDescription()
        captured["unit"] = band.GetUnitType()
        captured["nodata"] = band.GetNoDataValue()
        captured["value"] = band.ReadAsArray()[0, 0]
        return SimpleNamespace(output_key=output_key, cog_key="sfc_cog.tif")

    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    clear_cache = mocker.patch("wps_shared.utils.s3.gdal.VSICurlClearCache")
    mocker.patch(
        "wps_sfms.processors.surface_fuel_consumption.publish_dataset",
        side_effect=capture_publish,
    )

    await SurfaceFuelConsumptionProcessor(TEST_DATETIME).process(
        s3_client, make_dataset_context(datasets), inputs
    )

    assert captured == {
        "output_key": inputs.output_key,
        "description": "surface_fuel_consumption",
        "unit": "kg/m2",
        "nodata": pytest.approx(SFMS_NO_DATA),
        "value": pytest.approx(SFMS_NO_DATA),
    }
    clear_cache.assert_called_once_with()


@pytest.mark.anyio
async def test_processor_publish_failure_propagates_and_clears_cache(mocker: MockerFixture):
    datasets = make_datasets(np.array([[1]], dtype=np.float32))
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    processor = SurfaceFuelConsumptionProcessor(TEST_DATETIME)
    input_context = make_dataset_context(datasets)
    mocker.patch(
        "wps_sfms.processors.surface_fuel_consumption.publish_dataset",
        new=AsyncMock(side_effect=RuntimeError("COG generation failed")),
    )
    clear_cache = mocker.patch("wps_shared.utils.s3.gdal.VSICurlClearCache")

    with pytest.raises(RuntimeError, match="COG generation failed"):
        await processor.process(s3_client, input_context, inputs)

    clear_cache.assert_called_once_with()


@pytest.mark.anyio
async def test_processor_rejects_mismatched_grid(mocker: MockerFixture):
    datasets = make_datasets(np.array([[1]], dtype=np.float32))
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    processor = SurfaceFuelConsumptionProcessor(TEST_DATETIME)
    input_context = make_dataset_context(datasets)
    mocker.patch("wps_sfms.processors.surface_fuel_consumption.rasters_match", return_value=False)
    publish = mocker.patch(
        "wps_sfms.processors.surface_fuel_consumption.publish_dataset", new=AsyncMock()
    )

    with pytest.raises(ValueError, match="does not match the fuel grid"):
        await processor.process(s3_client, input_context, inputs)

    publish.assert_not_awaited()


@pytest.mark.anyio
async def test_processor_rejects_missing_dependency():
    inputs = make_inputs()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=False))
    processor = SurfaceFuelConsumptionProcessor(TEST_DATETIME)
    datasets = make_datasets(np.array([[1]]))
    input_context = make_dataset_context(datasets)

    with pytest.raises(RuntimeError, match="Missing SFC dependencies"):
        await processor.process(s3_client, input_context, inputs)

    s3_client.all_objects_exist.assert_awaited_once_with(
        inputs.fuel_key,
        inputs.ffmc_key,
        inputs.bui_key,
        inputs.percent_conifer_key,
    )
