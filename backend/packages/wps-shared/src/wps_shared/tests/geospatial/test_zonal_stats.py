import numpy as np
import pytest
from osgeo import gdal, osr

from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_raster_windows,
    pixel_area,
)


def create_raster(values: np.ndarray, geotransform=(0, 10, 0, 20, 0, -10)):
    dataset = gdal.GetDriverByName("MEM").Create(
        "", values.shape[1], values.shape[0], 1, gdal.GDT_Int32
    )
    dataset.SetGeoTransform(geotransform)
    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(3005)
    dataset.SetProjection(spatial_reference.ExportToWkt())
    dataset.GetRasterBand(1).WriteArray(values)
    return dataset


def test_count_values_by_zone_counts_only_included_pixels():
    zones = np.array([[1, 1, 2], [1, 2, 2]])
    values = np.array([[3, 3, 3], [2, 2, 3]])
    included_pixels = np.array([[True, True, True], [False, True, False]])

    counts = count_values_by_zone(zones, values, included_pixels)

    assert counts == {(1, 3): 2, (2, 3): 1, (2, 2): 1}


def test_count_values_by_zone_returns_empty_counter_without_included_pixels():
    zones = np.array([[1]])
    values = np.array([[3]])

    assert count_values_by_zone(zones, values, np.array([[False]])) == {}


def test_iter_raster_windows_reads_matching_chunks():
    first = create_raster(np.arange(12).reshape(3, 4))
    second = create_raster(np.arange(12, 24).reshape(3, 4))

    windows = list(iter_raster_windows([first, second], window_size=2))

    assert [(window.width, window.height) for window in windows] == [
        (2, 2),
        (2, 2),
        (2, 1),
        (2, 1),
    ]
    np.testing.assert_array_equal(windows[-1].arrays[1], [[22, 23]])


def test_iter_raster_windows_rejects_grid_difference():
    reference = create_raster(np.ones((2, 2)))
    shifted = create_raster(np.ones((2, 2)), geotransform=(1, 10, 0, 20, 0, -10))

    with pytest.raises(ValueError, match="does not match"):
        list(iter_raster_windows([reference, shifted]))


def test_iter_raster_windows_rejects_rotation_difference():
    reference = create_raster(np.ones((2, 2)))
    rotated = create_raster(np.ones((2, 2)), geotransform=(0, 10, 1, 20, 0, -10))

    with pytest.raises(ValueError, match="does not match"):
        list(iter_raster_windows([reference, rotated]))


def test_pixel_area():
    dataset = create_raster(np.array([[7, 8], [9, 10]]))

    assert pixel_area(dataset) == 100
