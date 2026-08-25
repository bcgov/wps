import numpy as np
from app.auto_spatial_advisory.process_fuel_type_area import (
    calculate_fuel_type_areas,
    classify_by_threshold,
)
from osgeo import gdal
from wps_shared.db.models.auto_spatial_advisory import SFMSFuelType

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
