from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import cffdrs.foliar_moisture_content
import numpy as np
import pytest
from osgeo import gdal, osr
from pytest_mock import MockerFixture
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.processors.foliar_moisture_content import (
    FoliarMoistureContentDatasets,
    FoliarMoistureContentProcessor,
    calculate_foliar_moisture_content,
    ensure_fmc_rasters,
)
from wps_sfms.raster_inputs import FoliarMoistureContentInputs

NODATA = -9999.0
MODULE_PATH = "wps_sfms.processors.foliar_moisture_content"


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
    elevation: np.ndarray,
    latitude: np.ndarray | None = None,
    longitude: np.ndarray | None = None,
) -> FoliarMoistureContentDatasets:
    shape = elevation.shape
    return FoliarMoistureContentDatasets(
        fuel=make_dataset("fuel.tif", np.ones(shape, dtype=np.float32)),
        elevation=make_dataset("elevation.tif", elevation),
        latitude=make_dataset(
            "latitude.tif",
            latitude if latitude is not None else np.full(shape, 49.0),
        ),
        longitude=make_dataset(
            "longitude.tif",
            longitude if longitude is not None else np.full(shape, -123.0),
        ),
    )


def test_calculation_matches_cffdrs_and_normalizes_western_longitude():
    target_date = date(2024, 5, 30)
    datasets = make_datasets(
        np.array([[100.0, 100.0]], dtype=np.float32),
        longitude=np.array([[-123.0, 123.0]], dtype=np.float32),
    )

    result = calculate_foliar_moisture_content(datasets, target_date)

    expected = cffdrs.foliar_moisture_content.foliar_moisture_content(
        49.0,
        123.0,
        100.0,
        151,
        0,
    )
    np.testing.assert_allclose(result.values, np.full((1, 2), expected, dtype=np.float32))


def test_static_input_nodata_propagates_to_output():
    datasets = make_datasets(
        np.array([[NODATA, 100.0, 100.0]], dtype=np.float32),
        latitude=np.array([[49.0, NODATA, 49.0]], dtype=np.float32),
        longitude=np.array([[-123.0, -123.0, NODATA]], dtype=np.float32),
    )

    result = calculate_foliar_moisture_content(datasets, date(2024, 7, 4))

    np.testing.assert_array_equal(
        result.values,
        np.full((1, 3), SFMS_NO_DATA, dtype=np.float32),
    )


def make_inputs(*target_dates: date) -> FoliarMoistureContentInputs:
    return FoliarMoistureContentInputs(
        fuel_key="/vsis3/test/sfms/fuel/2024/fuel.tif",
        elevation_key="/vsis3/test/sfms_ng/static/bc_elevation.tif",
        latitude_key="/vsis3/test/sfms_ng/static/latitude.tif",
        longitude_key="/vsis3/test/sfms_ng/static/longitude.tif",
        output_keys={
            target_date: f"sfms_ng/static/fmc/{target_date:%Y/%m/%d}/fmc_{target_date:%Y%m%d}.tif"
            for target_date in target_dates
        },
    )


def make_dataset_context(datasets: FoliarMoistureContentDatasets, calls: list[list[str]]):
    @contextmanager
    def dataset_context(keys):
        calls.append(keys)
        input_datasets = [
            datasets.fuel,
            datasets.elevation,
            datasets.latitude,
            datasets.longitude,
        ]
        for dataset, key in zip(input_datasets, keys, strict=True):
            dataset.ds_path = key
        yield input_datasets

    return dataset_context


@pytest.mark.anyio
async def test_processor_loads_static_inputs_once_and_publishes_each_date_with_metadata(
    mocker: MockerFixture,
):
    target_dates = (date(2024, 5, 30), date(2024, 5, 31))
    inputs = make_inputs(*target_dates)
    datasets = make_datasets(np.array([[100.0]], dtype=np.float32))
    context_calls = []
    captured = []

    async def capture_publish(*, dataset, output_key, **_kwargs):
        band = dataset.as_gdal_ds().GetRasterBand(1)
        captured.append(
            {
                "output_key": output_key,
                "description": band.GetDescription(),
                "unit": band.GetUnitType(),
                "nodata": band.GetNoDataValue(),
                "value": band.ReadAsArray()[0, 0],
            }
        )
        return SimpleNamespace(output_key=output_key, cog_key=f"{output_key}_cog")

    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    publish = mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.publish_dataset",
        side_effect=capture_publish,
    )

    await FoliarMoistureContentProcessor().process(
        s3_client,
        make_dataset_context(datasets, context_calls),
        inputs,
    )

    assert len(context_calls) == 1
    assert [item["output_key"] for item in captured] == list(inputs.output_keys.values())
    assert all(item["description"] == "foliar_moisture_content" for item in captured)
    assert all(item["unit"] == "%" for item in captured)
    assert all(item["nodata"] == pytest.approx(SFMS_NO_DATA) for item in captured)
    assert all(item["value"] != pytest.approx(SFMS_NO_DATA) for item in captured)
    assert publish.await_count == 2


@pytest.mark.anyio
async def test_processor_applies_bc_mask_to_published_output(
    mocker: MockerFixture,
    output_mask: WPSDataset,
):
    target_date = date(2024, 7, 4)
    inputs = make_inputs(target_date)
    datasets = make_datasets(np.array([[100.0]], dtype=np.float32))
    context_calls = []
    captured_value = None
    output_mask.as_gdal_ds().GetRasterBand(1).WriteArray(np.array([[0]], dtype=np.float32))

    async def capture_publish(*, dataset, output_key, **_kwargs):
        nonlocal captured_value
        captured_value = dataset.as_gdal_ds().GetRasterBand(1).ReadAsArray()[0, 0]
        return SimpleNamespace(output_key=output_key, cog_key=f"{output_key}_cog")

    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.publish_dataset",
        side_effect=capture_publish,
    )

    await FoliarMoistureContentProcessor().process(
        s3_client,
        make_dataset_context(datasets, context_calls),
        inputs,
    )

    assert captured_value == pytest.approx(SFMS_NO_DATA)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "mismatched_label,match_results",
    [
        ("elevation", [False]),
        ("latitude", [True, False]),
        ("longitude", [True, True, False]),
    ],
)
async def test_processor_rejects_static_grid_that_mismatches_fuel(
    mocker: MockerFixture,
    mismatched_label: str,
    match_results: list[bool],
):
    inputs = make_inputs(date(2024, 7, 4))
    datasets = make_datasets(np.array([[100.0]], dtype=np.float32))
    context_calls = []
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.rasters_match",
        side_effect=match_results,
    )
    publish = mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.publish_dataset",
        new=AsyncMock(),
    )

    with pytest.raises(ValueError, match=f"{mismatched_label} raster does not match the fuel grid"):
        await FoliarMoistureContentProcessor().process(
            s3_client,
            make_dataset_context(datasets, context_calls),
            inputs,
        )

    publish.assert_not_awaited()


@pytest.mark.anyio
async def test_processor_rejects_missing_static_dependency():
    inputs = make_inputs(date(2024, 7, 4))
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=False))

    with pytest.raises(RuntimeError, match="Missing FMC dependencies"):
        await FoliarMoistureContentProcessor().process(
            s3_client,
            lambda _keys: None,
            inputs,
        )

    s3_client.all_objects_exist.assert_awaited_once_with(
        inputs.fuel_key,
        inputs.elevation_key,
        inputs.latitude_key,
        inputs.longitude_key,
    )


@pytest.mark.anyio
async def test_processor_publish_failure_propagates_and_clears_cache(mocker: MockerFixture):
    inputs = make_inputs(date(2024, 7, 4))
    datasets = make_datasets(np.array([[100.0]], dtype=np.float32))
    context_calls = []
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=True))
    mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.publish_dataset",
        new=AsyncMock(side_effect=RuntimeError("COG generation failed")),
    )
    clear_cache = mocker.patch("wps_shared.utils.s3.gdal.VSICurlClearCache")
    action = FoliarMoistureContentProcessor().process(
        s3_client,
        make_dataset_context(datasets, context_calls),
        inputs,
    )

    with pytest.raises(RuntimeError, match="COG generation failed"):
        await action

    clear_cache.assert_called_once_with()


@pytest.mark.anyio
async def test_ensure_fmc_rasters_skips_complete_dates_and_processes_missing_dates(
    mocker: MockerFixture,
):
    existing_date = date(2025, 7, 4)
    missing_date = date(2025, 7, 5)
    addresser = MagicMock()
    addresser.get_fmc_key.side_effect = lambda target_date: f"fmc_{target_date:%Y%m%d}.tif"
    addresser.get_cog_key.side_effect = lambda key: f"/vsis3/test/{key[:-4]}_cog.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/test/{key}"
    fmc_inputs = MagicMock()
    addresser.get_fmc_inputs.return_value = fmc_inputs
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(side_effect=[True, False])
    processor = MagicMock()
    processor.process = AsyncMock()
    processor_class = mocker.patch(
        f"{MODULE_PATH}.FoliarMoistureContentProcessor",
        return_value=processor,
    )
    fuel = make_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    existing_fmc = make_dataset("fmc.tif", np.ones((1, 1), dtype=np.float32))

    open_dataset = mocker.patch(f"{MODULE_PATH}.WPSDataset", side_effect=[fuel, existing_fmc])

    await ensure_fmc_rasters(
        [existing_date, existing_date, missing_date],
        "fuel.tif",
        addresser,
        s3_client,
    )

    assert s3_client.all_objects_exist.await_args_list[0].args == (
        "fmc_20250704.tif",
        "/vsis3/test/fmc_20250704_cog.tif",
    )
    assert s3_client.all_objects_exist.await_args_list[1].args == (
        "fmc_20250705.tif",
        "/vsis3/test/fmc_20250705_cog.tif",
    )
    addresser.get_fmc_inputs.assert_called_once_with([missing_date], "fuel.tif")
    processor_class.assert_called_once_with()
    processor.process.assert_awaited_once()
    assert processor.process.await_args.args[0] is s3_client
    assert processor.process.await_args.args[2] is fmc_inputs
    assert [item.args[0] for item in open_dataset.call_args_list] == [
        "fuel.tif",
        "/vsis3/test/fmc_20250704.tif",
    ]


@pytest.mark.anyio
async def test_ensure_fmc_rasters_does_not_load_static_inputs_when_all_outputs_match(
    mocker: MockerFixture,
):
    target_date = date(2025, 7, 4)
    addresser = MagicMock()
    addresser.get_fmc_key.return_value = "fmc_20250704.tif"
    addresser.get_cog_key.return_value = "/vsis3/test/fmc_20250704_cog.tif"
    addresser.gdal_path.return_value = "/vsis3/test/fmc_20250704.tif"
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    processor_class = mocker.patch(f"{MODULE_PATH}.FoliarMoistureContentProcessor")
    fuel = make_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    existing_fmc = make_dataset("fmc.tif", np.ones((1, 1), dtype=np.float32))

    mocker.patch(f"{MODULE_PATH}.WPSDataset", side_effect=[fuel, existing_fmc])

    await ensure_fmc_rasters([target_date], "fuel.tif", addresser, s3_client)

    addresser.get_fmc_inputs.assert_not_called()
    processor_class.assert_not_called()


@pytest.mark.anyio
async def test_ensure_fmc_rasters_rejects_existing_output_that_mismatches_fuel(
    mocker: MockerFixture,
):
    target_date = date(2025, 7, 4)
    addresser = MagicMock()
    addresser.get_fmc_key.return_value = "fmc_20250704.tif"
    addresser.get_cog_key.return_value = "/vsis3/test/fmc_20250704_cog.tif"
    addresser.gdal_path.return_value = "/vsis3/test/fmc_20250704.tif"
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    processor_class = mocker.patch(f"{MODULE_PATH}.FoliarMoistureContentProcessor")
    fuel = make_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    existing_fmc = make_dataset("fmc.tif", np.ones((2, 1), dtype=np.float32))

    mocker.patch(f"{MODULE_PATH}.WPSDataset", side_effect=[fuel, existing_fmc])
    action = ensure_fmc_rasters([target_date], "fuel.tif", addresser, s3_client)

    with pytest.raises(ValueError, match="Existing FMC raster for 2025-07-04"):
        await action

    processor_class.assert_not_called()
