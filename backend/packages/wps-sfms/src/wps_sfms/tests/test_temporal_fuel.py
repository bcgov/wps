from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest
from osgeo import gdal
from pytest_mock import MockerFixture
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.schemas.sfms import FuelCodesLookup

from wps_sfms.processors.temporal_fuel import (
    TemporalFuelDatasets,
    calculate_temporal_fuel,
    fuel_codes_lookup,
    publish_temporal_fuel_raster,
)
from wps_sfms.tests.raster_test_utils import TEST_INPUT_NODATA, create_test_wps_dataset

# interim green-up rasters: on Jun 1 (day 152), off Sep 15 (day 258)
GREEN_UP_ON = np.full((1, 5), 152.0)
GREEN_UP_OFF = np.full((1, 5), 258.0)
# BC base values: D-1, M-1, C-3, non-fuel, nodata
BASE_FUEL = np.array([[8, 14, 3, 99, TEST_INPUT_NODATA]])


def make_datasets(
    base_fuel: np.ndarray, green_up_on: np.ndarray, green_up_off: np.ndarray
) -> TemporalFuelDatasets:
    return TemporalFuelDatasets(
        base_fuel=create_test_wps_dataset("base_fuel.tif", base_fuel),
        green_up_on=create_test_wps_dataset("green_up_on.tif", green_up_on),
        green_up_off=create_test_wps_dataset("green_up_off.tif", green_up_off),
    )


@pytest.mark.parametrize(
    "target_date,expected",
    [
        (date(2026, 5, 31), [11, 40, 3, 101, np.nan]),  # day 151, before green-up
        (date(2026, 6, 1), [12, 50, 3, 101, np.nan]),  # day 152, first green day
        (date(2026, 9, 14), [12, 50, 3, 101, np.nan]),  # day 257, last green day
        (date(2026, 9, 15), [11, 40, 3, 101, np.nan]),  # day 258, leafless again
    ],
)
def test_translates_base_fuel_and_applies_green_up(target_date: date, expected: list):
    result = calculate_temporal_fuel(
        make_datasets(BASE_FUEL, GREEN_UP_ON, GREEN_UP_OFF), target_date
    )

    np.testing.assert_array_equal(result, np.array([expected], dtype=np.float32))


def test_julian_nodata_never_greens_up():
    datasets = make_datasets(
        np.array([[8, 8]]),
        np.array([[TEST_INPUT_NODATA, 152.0]]),
        np.array([[258.0, TEST_INPUT_NODATA]]),
    )

    result = calculate_temporal_fuel(datasets, date(2026, 7, 1))

    np.testing.assert_array_equal(result, np.array([[11, 11]], dtype=np.float32))


@pytest.mark.parametrize("value", [0, 15, 101, 1.5])
def test_rejects_unsupported_base_fuel_values(value: float):
    datasets = make_datasets(np.array([[value]]), GREEN_UP_ON[:, :1], GREEN_UP_OFF[:, :1])

    with pytest.raises(ValueError, match="unsupported classifications"):
        calculate_temporal_fuel(datasets, date(2026, 7, 1))


def test_fuel_codes_lookup_lists_present_grid_values_in_order():
    temporal = np.array([[50, 12, 101, 12, np.nan]], dtype=np.float32)

    result = fuel_codes_lookup(temporal)

    assert [row.grid_value for row in result.root] == [12, 50, 101]
    assert result.root[0].model_dump() == {
        "grid_value": 12,
        "export_value": 12,
        "descriptive_name": "Green Aspen (with BUI Thresholding)",
        "fuel_type": "D-2",
        "r": 137,
        "g": 112,
        "b": 68,
        "h": 27,
        "s": 86,
        "l": 103,
    }


BASE_NODATA = -10000.0


def write_tif(
    path: Path, values: np.ndarray, datatype: int, nodata: float | None = None, x_origin=0.0
) -> str:
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), values.shape[1], values.shape[0], 1, datatype
    )
    ds.SetGeoTransform((x_origin, 2000, 0, 0, 0, -2000))
    ds.SetProjection("EPSG:3005")
    band = ds.GetRasterBand(1)
    band.WriteArray(values)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    ds = None
    return str(path)


@pytest.fixture
def rasters(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        base=write_tif(
            tmp_path / "base.tif",
            np.array([[8, 14, 3, BASE_NODATA]], dtype=np.float32),
            gdal.GDT_Float32,
            BASE_NODATA,
        ),
        on=write_tif(tmp_path / "on.tif", np.full((1, 4), 152, dtype=np.int16), gdal.GDT_Int16),
        off=write_tif(tmp_path / "off.tif", np.full((1, 4), 258, dtype=np.int16), gdal.GDT_Int16),
    )


@pytest.fixture
def s3_client() -> SimpleNamespace:
    return SimpleNamespace(
        all_objects_exist=AsyncMock(return_value=True),
        put_object=AsyncMock(),
        get_content_hash=AsyncMock(return_value="temporal-hash"),
    )


@pytest.mark.anyio
async def test_publish_temporal_fuel_raster_stores_grid_and_fuel_codes_lookup(
    mocker: MockerFixture, rasters: SimpleNamespace, s3_client: SimpleNamespace
):
    published = {}

    async def capture_publish(_s3_client, dataset, output_key, cog_resample_alg):
        band = dataset.as_gdal_ds().GetRasterBand(1)
        published.update(
            output_key=output_key,
            values=band.ReadAsArray(),
            datatype=band.DataType,
            nodata=band.GetNoDataValue(),
            cog_resample_alg=cog_resample_alg,
        )
        return SimpleNamespace(output_key=output_key, cog_key=f"{output_key}_cog")

    mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset", side_effect=capture_publish)

    content_hash = await publish_temporal_fuel_raster(
        s3_client,
        rasters.base,
        rasters.on,
        rasters.off,
        date(2026, 7, 1),
        "temporal/fbp.tif",
        "temporal/fbp.json",
    )

    assert content_hash == "temporal-hash"
    s3_client.get_content_hash.assert_awaited_once_with("temporal/fbp.tif")
    assert published["output_key"] == "temporal/fbp.tif"
    # green on Jul 1: D-1 -> D-2 (12), M-1 -> M-2 (50); nodata keeps the base grid's value
    np.testing.assert_array_equal(
        published["values"], np.array([[12, 50, 3, BASE_NODATA]], dtype=np.float32)
    )
    assert published["datatype"] == gdal.GDT_Float32
    assert published["nodata"] == BASE_NODATA
    assert published["cog_resample_alg"] == GDALResamplingMethod.NEAREST_NEIGHBOUR

    s3_client.put_object.assert_awaited_once()
    put_kwargs = s3_client.put_object.await_args.kwargs
    assert put_kwargs["key"] == "temporal/fbp.json"
    lookup = FuelCodesLookup.model_validate_json(put_kwargs["body"])
    assert [row.grid_value for row in lookup.root] == [3, 12, 50]


@pytest.mark.anyio
async def test_publish_temporal_fuel_raster_rejects_misaligned_green_up_raster(
    mocker: MockerFixture, tmp_path: Path, rasters: SimpleNamespace, s3_client: SimpleNamespace
):
    shifted_on = write_tif(
        tmp_path / "shifted_on.tif",
        np.full((1, 4), 152, dtype=np.int16),
        gdal.GDT_Int16,
        x_origin=2000.0,
    )
    publish = mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset")

    with pytest.raises(ValueError, match="green_up_on raster does not match the fuel grid"):
        await publish_temporal_fuel_raster(
            s3_client,
            rasters.base,
            shifted_on,
            rasters.off,
            date(2026, 7, 1),
            "temporal/fbp.tif",
            "temporal/fbp.json",
        )

    publish.assert_not_called()
    s3_client.put_object.assert_not_awaited()


@pytest.mark.anyio
async def test_publish_temporal_fuel_raster_requires_all_inputs(
    mocker: MockerFixture, rasters: SimpleNamespace, s3_client: SimpleNamespace
):
    s3_client.all_objects_exist = AsyncMock(return_value=False)
    publish = mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset")

    with pytest.raises(RuntimeError, match="Missing raster dependencies"):
        await publish_temporal_fuel_raster(
            s3_client,
            rasters.base,
            rasters.on,
            rasters.off,
            date(2026, 7, 1),
            "temporal/fbp.tif",
            "temporal/fbp.json",
        )

    publish.assert_not_called()
