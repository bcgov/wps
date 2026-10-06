from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest
from osgeo import gdal
from pytest_mock import MockerFixture
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.schemas.sfms import FuelCodesLookup

from wps_sfms.fbp_fuel_types import CFFDRSFuelTypes
from wps_sfms.processors.temporal_fuel import (
    TemporalFuelInputDatasets,
    TemporalFuelGrid,
    publish_temporal_fuel_raster,
)
from wps_sfms.tests.raster_test_utils import TEST_INPUT_NODATA, create_test_wps_dataset

# interim Julian date rasters: green-up Jun 1 (152) to Sep 15 (258), grass standing Jun 1 (152)
# to Dec 1 (335)
JULIAN_DAYS = {
    "green_up_on": 152.0,
    "green_up_off": 258.0,
    "grass_standing": 152.0,
    "grass_matted": 335.0,
}
# BC base values: D-1, M-1, C-3, O-1a, non-fuel, nodata
BASE_FUEL = np.array([[8, 14, 3, 12, 99, TEST_INPUT_NODATA]])


def test_bc_grid_values_translate_to_national_lookup_values():
    assert set(TemporalFuelGrid.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.values()) <= set(
        TemporalFuelGrid.NATIONAL_FUEL_LOOKUP
    )
    assert TemporalFuelGrid.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[8] == 11  # D-1
    assert TemporalFuelGrid.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[12] == 31  # O-1a
    assert TemporalFuelGrid.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[14] == 40  # M-1
    assert TemporalFuelGrid.NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[99] == 101  # Non-fuel


NATIONAL_FUEL_TYPES = CFFDRSFuelTypes.from_lookup(
    FuelCodesLookup(fuel_codes=list(TemporalFuelGrid.NATIONAL_FUEL_LOOKUP.values()))
).by_grid_value


@pytest.mark.parametrize(
    "swaps,expected",
    [
        (TemporalFuelGrid.GREEN_UP_GRID_VALUES, {"D1": "D2", "M1": "M2", "M3": "M4"}),
        (TemporalFuelGrid.GRASS_STANDING_GRID_VALUES, {"O1A": "O1B"}),
    ],
)
def test_seasonal_swaps_map_to_their_cffdrs_fuel_types(swaps, expected):
    assert {
        NATIONAL_FUEL_TYPES[before]: NATIONAL_FUEL_TYPES[after] for before, after in swaps.items()
    } == expected


def make_datasets(base_fuel: np.ndarray, **julian: np.ndarray) -> TemporalFuelInputDatasets:
    """Build input datasets, using the interim Julian days for any raster not given."""
    julian_values = {
        name: julian.get(name, np.full(base_fuel.shape, day)) for name, day in JULIAN_DAYS.items()
    }
    return TemporalFuelInputDatasets(
        base_fuel=create_test_wps_dataset("base_fuel.tif", base_fuel),
        **{
            name: create_test_wps_dataset(f"{name}.tif", values)
            for name, values in julian_values.items()
        },
    )


@pytest.mark.parametrize(
    "target_date,expected",
    [
        (date(2026, 5, 31), [11, 40, 3, 31, 101, np.nan]),  # day 151, leafless and matted
        (date(2026, 6, 1), [12, 50, 3, 32, 101, np.nan]),  # day 152, first green and standing day
        (date(2026, 9, 14), [12, 50, 3, 32, 101, np.nan]),  # day 257, last green day
        (date(2026, 9, 15), [11, 40, 3, 32, 101, np.nan]),  # day 258, leafless, still standing
        (date(2026, 11, 30), [11, 40, 3, 32, 101, np.nan]),  # day 334, last standing day
        (date(2026, 12, 1), [11, 40, 3, 31, 101, np.nan]),  # day 335, matted again
        # leap years switch on the same calendar dates
        (date(2028, 5, 31), [11, 40, 3, 31, 101, np.nan]),
        (date(2028, 6, 1), [12, 50, 3, 32, 101, np.nan]),
        (date(2028, 9, 14), [12, 50, 3, 32, 101, np.nan]),
        (date(2028, 9, 15), [11, 40, 3, 32, 101, np.nan]),
        (date(2028, 11, 30), [11, 40, 3, 32, 101, np.nan]),
        (date(2028, 12, 1), [11, 40, 3, 31, 101, np.nan]),
    ],
)
def test_translates_base_fuel_and_applies_green_up_and_grass_curing(
    target_date: date, expected: list
):
    result = TemporalFuelGrid.build(make_datasets(BASE_FUEL), target_date).values

    np.testing.assert_array_equal(result, np.array([expected], dtype=np.float32))


@pytest.mark.parametrize(
    "julian_name,base_value,unchanged_value",
    [
        ("green_up_on", 8, 11),
        ("green_up_off", 8, 11),
        ("grass_standing", 12, 31),
        ("grass_matted", 12, 31),
    ],
)
def test_julian_nodata_never_switches(julian_name: str, base_value: int, unchanged_value: int):
    datasets = make_datasets(
        np.array([[base_value]]), **{julian_name: np.array([[TEST_INPUT_NODATA]])}
    )

    result = TemporalFuelGrid.build(datasets, date(2026, 7, 1)).values

    np.testing.assert_array_equal(result, np.array([[unchanged_value]], dtype=np.float32))


@pytest.mark.parametrize("value", [0, 15, 101, 1.5])
def test_rejects_unsupported_base_fuel_values(value: float):
    datasets = make_datasets(np.array([[value]]))

    target_date = date(2026, 7, 1)

    with pytest.raises(ValueError, match="unsupported classifications"):
        TemporalFuelGrid.build(datasets, target_date)


def test_fuel_codes_lookup_lists_present_grid_values_in_order():
    temporal = np.array([[50, 12, 101, 12, np.nan]], dtype=np.float32)

    result = TemporalFuelGrid(temporal).fuel_codes_lookup()

    assert [row.grid_value for row in result.fuel_codes] == [12, 50, 101]
    assert result.fuel_codes[0].model_dump() == {
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
        base_fuel_key=write_tif(
            tmp_path / "base.tif",
            np.array([[8, 14, 3, 12, BASE_NODATA]], dtype=np.float32),
            gdal.GDT_Float32,
            BASE_NODATA,
        ),
        **{
            f"{name}_key": write_tif(
                tmp_path / f"{name}.tif", np.full((1, 5), day, dtype=np.int16), gdal.GDT_Int16
            )
            for name, day in JULIAN_DAYS.items()
        },
    )


@pytest.fixture
def s3_client() -> SimpleNamespace:
    return SimpleNamespace(
        all_objects_exist=AsyncMock(return_value=True),
        put_object=AsyncMock(),
    )


def open_from_file(path: str) -> WPSDataset:
    return WPSDataset.from_bytes(Path(path).read_bytes())


async def publish(
    s3_client,
    target_date: date,
    *,
    base_fuel_key: str,
    green_up_on_key: str,
    green_up_off_key: str,
    grass_standing_key: str,
    grass_matted_key: str,
) -> str:
    """Publish with each Julian raster opened from its bytes, as resolve_temporal_fuel_raster does."""
    with (
        open_from_file(green_up_on_key) as green_up_on,
        open_from_file(green_up_off_key) as green_up_off,
        open_from_file(grass_standing_key) as grass_standing,
        open_from_file(grass_matted_key) as grass_matted,
    ):
        return await publish_temporal_fuel_raster(
            s3_client,
            target_date,
            base_fuel_key=base_fuel_key,
            green_up_on=green_up_on,
            green_up_off=green_up_off,
            grass_standing=grass_standing,
            grass_matted=grass_matted,
            output_key="temporal/fbp.tif",
            fuel_codes_lookup_key="temporal/fbp.json",
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
        return SimpleNamespace(
            output_key=output_key, cog_key=f"{output_key}_cog", content_hash="temporal-hash"
        )

    mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset", side_effect=capture_publish)

    content_hash = await publish(s3_client, date(2026, 7, 1), **vars(rasters))

    assert content_hash == "temporal-hash"
    assert published["output_key"] == "temporal/fbp.tif"
    # Jul 1: D-1 -> D-2 (12), M-1 -> M-2 (50), O-1a -> O-1b (32); nodata keeps the base value
    np.testing.assert_array_equal(
        published["values"], np.array([[12, 50, 3, 32, BASE_NODATA]], dtype=np.float32)
    )
    assert published["datatype"] == gdal.GDT_Float32
    assert published["nodata"] == BASE_NODATA
    assert published["cog_resample_alg"] == GDALResamplingMethod.NEAREST_NEIGHBOUR

    s3_client.put_object.assert_awaited_once()
    put_kwargs = s3_client.put_object.await_args.kwargs
    assert put_kwargs["key"] == "temporal/fbp.json"
    lookup = FuelCodesLookup.model_validate_json(put_kwargs["body"])
    assert [row.grid_value for row in lookup.fuel_codes] == [3, 12, 32, 50]


@pytest.mark.anyio
@pytest.mark.parametrize("julian_name", ["green_up_on", "grass_matted"])
async def test_publish_temporal_fuel_raster_rejects_misaligned_julian_raster(
    mocker: MockerFixture,
    tmp_path: Path,
    rasters: SimpleNamespace,
    s3_client: SimpleNamespace,
    julian_name: str,
):
    shifted = write_tif(
        tmp_path / f"shifted_{julian_name}.tif",
        np.full((1, 5), 152, dtype=np.int16),
        gdal.GDT_Int16,
        x_origin=2000.0,
    )
    keys = {**vars(rasters), f"{julian_name}_key": shifted}
    target_date = date(2026, 7, 1)
    publish_dataset = mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset")

    with pytest.raises(ValueError, match=f"{julian_name} raster does not match the fuel grid"):
        await publish(s3_client, target_date, **keys)

    publish_dataset.assert_not_called()
    s3_client.put_object.assert_not_awaited()


@pytest.mark.anyio
async def test_publish_temporal_fuel_raster_requires_all_inputs(
    mocker: MockerFixture, rasters: SimpleNamespace, s3_client: SimpleNamespace
):
    s3_client.all_objects_exist = AsyncMock(return_value=False)
    publish_dataset = mocker.patch("wps_sfms.processors.temporal_fuel.publish_dataset")
    keys = vars(rasters)
    target_date = date(2026, 7, 1)

    with pytest.raises(RuntimeError, match="Missing raster dependencies"):
        await publish(s3_client, target_date, **keys)

    publish_dataset.assert_not_called()
    # the Julian rasters arrive open, so only the base fuel raster is checked in object storage
    s3_client.all_objects_exist.assert_awaited_once_with(rasters.base_fuel_key)
