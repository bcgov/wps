from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from app.auto_spatial_advisory.process_fuel_type_area import (
    calculate_fuel_type_area_by_shape,
    calculate_fuel_type_areas,
    classify_by_threshold,
    get_advisory_shape,
    get_intersected_raster_path,
    intersect_raster_by_advisory_shape,
    process_fuel_type_hfi_by_shape,
)
from osgeo import gdal, ogr, osr
from wps_shared.db.models.auto_spatial_advisory import SFMSFuelType
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset
from wps_shared.run_type import RunType

HFI_RASTER = np.array(
    [
        [1000, 2000, 3000, 4005],
        [5000, 10001, 11000, 12000],
        [300, 500, 7006, 9000],
        [400, 0, 1, 300],
    ]
)


def test_classify_by_threshold_1():
    result = classify_by_threshold(HFI_RASTER, 1)
    # Sum array of zeros and ones, result will be a count of values from 4k - 10k.
    assert result.sum() == 4


def test_classify_by_threshold_2():
    result = classify_by_threshold(HFI_RASTER, 2)
    # Sum array of zeros and ones, result will be a count of values > 10k.
    assert result.sum() == 3


def _make_fuel_type_raster(data: np.ndarray, pixel_size: float) -> gdal.Dataset:
    ds = gdal.GetDriverByName("MEM").Create("test", data.shape[1], data.shape[0], 1, gdal.GDT_Byte)
    ds.SetGeoTransform((0, pixel_size, 0, 0, 0, -pixel_size))
    ds.GetRasterBand(1).WriteArray(data)
    return ds


def test_calculate_fuel_type_areas():
    # 10x10 raster, 100m x 100m pixels -> 10,000 m^2 per pixel.
    data = np.zeros((10, 10), dtype=np.uint8)
    data[0, 0:10] = 1  # 10 pixels of fuel type 1
    data[1, 0:5] = 2  # 5 pixels of fuel type 2
    data[2:6, 0:5] = 99  # 20 pixels of non-fuel (id 99), must be excluded
    ds = _make_fuel_type_raster(data, pixel_size=100)

    fuel_types = [
        SFMSFuelType(fuel_type_id=1, fuel_type_code="C1"),
        SFMSFuelType(fuel_type_id=2, fuel_type_code="C2"),
        SFMSFuelType(fuel_type_id=3, fuel_type_code="C3"),  # in lookup, absent from raster
        SFMSFuelType(fuel_type_id=99, fuel_type_code="NF"),  # non-fuel, excluded by id filter
    ]

    result = calculate_fuel_type_areas(ds, fuel_types)

    # fuel_type_id 3 has zero pixels (area 0) so it's excluded; 99 is excluded by the id filter.
    assert result == {1: 10 * 100 * 100, 2: 5 * 100 * 100}


def test_calculate_fuel_type_areas_excludes_ids_outside_valid_range():
    data = np.zeros((4, 4), dtype=np.uint8)
    data[0, :] = 0  # id 0 - excluded by filter (id must be > 0)
    data[1, :] = 99  # id 99 - excluded by filter (id must be < 99)
    data[2, :] = 5  # id 5 - combustible, included
    ds = _make_fuel_type_raster(data, pixel_size=10)

    fuel_types = [
        SFMSFuelType(fuel_type_id=0, fuel_type_code="NF0"),
        SFMSFuelType(fuel_type_id=99, fuel_type_code="NF99"),
        SFMSFuelType(fuel_type_id=5, fuel_type_code="C5"),
    ]

    result = calculate_fuel_type_areas(ds, fuel_types)

    assert result == {5: 4 * 10 * 10}


MODULE_PATH = "app.auto_spatial_advisory.process_fuel_type_area"


@pytest.mark.anyio
async def test_intersect_raster_by_advisory_shape_clips_to_shape_geometry(mocker):
    """The whole raster is filled with fuel type 50; only a 4x4 window is overwritten with fuel
    type 1. If clip_to_geometry didn't restrict to the advisory shape, 50 would show up too."""
    data = np.full((10, 10), 50, dtype=np.int16)
    data[3:7, 3:7] = 1
    fuel_type_ds = WPSDataset.from_array(
        data,
        Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005")),
        datatype=gdal.GDT_Int16,
    )

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    cutline = ogr.CreateGeometryFromWkt("POLYGON((-5 -5, 5 -5, 5 5, -5 5, -5 -5))")
    cutline.AssignSpatialReference(srs)
    mocker.patch(f"{MODULE_PATH}.get_advisory_shape", new=AsyncMock(return_value=cutline))

    with await intersect_raster_by_advisory_shape(
        AsyncMock(), threshold=1, advisory_shape_id=7, source_identifier="zoneA",
        masked_fuel_type_ds=fuel_type_ds,
    ) as intersected_ds:
        assert intersected_ds.as_gdal_ds().GetFileList() == [
            get_intersected_raster_path("zoneA", 1)
        ]
        assert np.array_equal(
            intersected_ds.ds.GetRasterBand(1).ReadAsArray(), np.full((4, 4), 1)
        )

    fuel_type_ds.close()


@pytest.mark.anyio
async def test_calculate_fuel_type_area_by_shape_stores_stats_per_advisory_shape(mocker):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.all.return_value = [(1, "zoneA"), (2, "zoneB")]
    session.execute = AsyncMock(return_value=result_mock)

    zone_a_ds = WPSDataset.from_array(
        np.array([[1, 1], [1, 99]], dtype=np.int16),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        datatype=gdal.GDT_Int16,
    )
    zone_b_ds = WPSDataset.from_array(
        np.array([[2, 2], [2, 1]], dtype=np.int16),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        datatype=gdal.GDT_Int16,
    )
    mock_intersect = mocker.patch(
        f"{MODULE_PATH}.intersect_raster_by_advisory_shape",
        new=AsyncMock(side_effect=[zone_a_ds, zone_b_ds]),
    )
    mock_store = mocker.patch(f"{MODULE_PATH}.store_advisory_fuel_stats", new=AsyncMock())

    fuel_types = [
        SFMSFuelType(fuel_type_id=1, fuel_type_code="C1"),
        SFMSFuelType(fuel_type_id=2, fuel_type_code="C2"),
    ]
    masked_fuel_type_ds = MagicMock()

    await calculate_fuel_type_area_by_shape(
        session, masked_fuel_type_ds, threshold=1, run_parameters_id=99, fuel_types=fuel_types,
        fuel_type_raster_id=10,
    )

    assert mock_intersect.call_args_list[0].args == (session, 1, 1, "zoneA", masked_fuel_type_ds)
    assert mock_intersect.call_args_list[1].args == (session, 1, 2, "zoneB", masked_fuel_type_ds)

    # zone_a_ds: fuel type 1 has 3 pixels (99 excluded, not in fuel_types); zone_b_ds: fuel type 2
    # has 3 pixels, fuel type 1 has 1 pixel - each pixel is 1x1.
    assert mock_store.call_args_list[0].args == (session, {1: 3}, 1, 99, 1, 10)
    assert mock_store.call_args_list[1].args == (session, {2: 3, 1: 1}, 1, 99, 2, 10)


@pytest.mark.anyio
async def test_get_advisory_shape_transforms_to_target_projection():
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar.return_value = (
        "POLYGON((1200000 500000, 1200100 500000, 1200100 500100, "
        "1200000 500100, 1200000 500000))"
    )
    session.execute = AsyncMock(return_value=result_mock)

    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    geometry = await get_advisory_shape(session, advisory_shape_id=1, projection=target_srs)

    # BC Albers (EPSG:3005) metre coordinates reprojected into WGS84 lon/lat.
    min_x, max_x, min_y, max_y = geometry.GetEnvelope()
    assert -180 <= min_x <= max_x <= 180
    assert -90 <= min_y <= max_y <= 90


@pytest.mark.anyio
async def test_process_fuel_type_hfi_by_shape_raises_if_no_fuel_type_raster(mocker):
    session = AsyncMock()
    mock_session_scope = mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope")
    mock_session_scope.return_value.__aenter__.return_value = session

    mocker.patch(f"{MODULE_PATH}.get_run_parameters_id", new=AsyncMock(return_value=1))
    mocker.patch(f"{MODULE_PATH}.get_fuel_type_raster_by_year", new=AsyncMock(return_value=None))

    with pytest.raises(RuntimeError, match="No fuel type raster found"):
        await process_fuel_type_hfi_by_shape(
            RunType.FORECAST, datetime(2024, 5, 1), date(2024, 5, 1)
        )


@pytest.mark.anyio
async def test_process_fuel_type_hfi_by_shape_skips_if_already_processed(mocker):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = MagicMock()  # a row already exists
    session.execute = AsyncMock(return_value=result_mock)
    mock_session_scope = mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope")
    mock_session_scope.return_value.__aenter__.return_value = session

    mocker.patch(f"{MODULE_PATH}.get_run_parameters_id", new=AsyncMock(return_value=1))
    mocker.patch(
        f"{MODULE_PATH}.get_fuel_type_raster_by_year",
        new=AsyncMock(return_value=MagicMock(id=10)),
    )
    mock_thresholds = mocker.patch(f"{MODULE_PATH}.get_all_hfi_thresholds", new=AsyncMock())

    await process_fuel_type_hfi_by_shape(RunType.FORECAST, datetime(2024, 5, 1), date(2024, 5, 1))

    mock_thresholds.assert_not_called()


@pytest.mark.anyio
async def test_process_fuel_type_hfi_by_shape_processes_each_threshold(mocker):
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None  # not processed yet
    session.execute = AsyncMock(return_value=result_mock)
    mock_session_scope = mocker.patch(f"{MODULE_PATH}.get_async_write_session_scope")
    mock_session_scope.return_value.__aenter__.return_value = session

    mocker.patch(f"{MODULE_PATH}.get_run_parameters_id", new=AsyncMock(return_value=1))
    mocker.patch(
        f"{MODULE_PATH}.get_fuel_type_raster_by_year",
        new=AsyncMock(return_value=MagicMock(id=10, object_store_path="fuel_type.tif")),
    )
    mocker.patch(f"{MODULE_PATH}.get_hfi_s3_key", return_value="/vsimem/test_hfi.tif")
    mocker.patch(f"{MODULE_PATH}.BaseRasterAddresser.gdal_path", return_value="/vsimem/test_ft.tif")

    hfi_ds = WPSDataset.from_array(
        np.array([[3000, 5000], [11000, 9000]], dtype=np.float32),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        output_path="/vsimem/test_hfi.tif",
    )
    fuel_type_ds = WPSDataset.from_array(
        np.array([[1, 2], [3, 4]], dtype=np.float32),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        output_path="/vsimem/test_ft.tif",
    )

    advisory_threshold = MagicMock(id=1)
    warning_threshold = MagicMock(id=2)
    mocker.patch(
        f"{MODULE_PATH}.get_all_hfi_thresholds",
        new=AsyncMock(return_value=[advisory_threshold, warning_threshold]),
    )
    fuel_types = [SFMSFuelType(fuel_type_id=1, fuel_type_code="C1")]
    mocker.patch(f"{MODULE_PATH}.get_all_sfms_fuel_types", new=AsyncMock(return_value=fuel_types))

    # calculate_fuel_type_area_by_shape closes masked_fuel_type_ds via its own `with` block on
    # return, so snapshot the array while the call is live rather than reading it afterwards.
    masked_arrays = []

    async def _snapshot_masked_array(_session, masked_fuel_type_ds, *_args):
        masked_arrays.append(masked_fuel_type_ds.ds.GetRasterBand(1).ReadAsArray().copy())

    mock_calculate_by_shape = mocker.patch(
        f"{MODULE_PATH}.calculate_fuel_type_area_by_shape",
        new=AsyncMock(side_effect=_snapshot_masked_array),
    )

    await process_fuel_type_hfi_by_shape(RunType.FORECAST, datetime(2024, 5, 1), date(2024, 5, 1))

    assert mock_calculate_by_shape.call_count == 2

    # threshold 1 (advisory, 4k-10k): [[3000, 5000], [11000, 9000]] -> [[0, 1], [0, 1]]
    advisory_call = mock_calculate_by_shape.call_args_list[0]
    assert np.array_equal(masked_arrays[0], [[0, 2], [0, 4]])
    assert advisory_call.args[2:] == (1, 1, fuel_types, 10)

    # threshold 2 (warning, >= 10k): [[3000, 5000], [11000, 9000]] -> [[0, 0], [1, 0]]
    warning_call = mock_calculate_by_shape.call_args_list[1]
    assert np.array_equal(masked_arrays[1], [[0, 0], [3, 0]])
    assert warning_call.args[2:] == (2, 1, fuel_types, 10)

    hfi_ds.close()
    fuel_type_ds.close()
