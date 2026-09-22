from collections import Counter

import numpy as np
import pytest
from osgeo import gdal, osr

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_aligned_raster_windows,
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
    return WPSDataset(ds_path=None, ds=dataset)


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


@pytest.mark.parametrize(
    "categories",
    [[1, 2], [1, 2, 3], [1, 2, 7, 14, 98]],
    ids=["hfi", "tpi", "fuel"],
)
def test_count_values_by_zone_matches_pair_counting(categories):
    rng = np.random.default_rng(42)
    zones = rng.choice(np.array([7, 101, 300], dtype=np.int32), size=(32, 32))
    values = rng.choice(categories, size=zones.shape)
    included_pixels = rng.random(zones.shape) > 0.3
    zones[~included_pixels] = -1
    values[~included_pixels] = -9999

    pairs, frequencies = np.unique(
        np.column_stack((zones[included_pixels], values[included_pixels])),
        axis=0,
        return_counts=True,
    )
    expected = {tuple(pair): int(count) for pair, count in zip(pairs.tolist(), frequencies)}

    assert count_values_by_zone(zones, values, included_pixels) == expected


@pytest.mark.parametrize("categories", [[0, 0, 0], [0, 98, 98]])
def test_count_values_by_zone_handles_zero_categories_and_sparse_zone_ids(categories):
    zones = np.array([[0, 300, 300]], dtype=np.int32)
    values = np.array([categories], dtype=np.uint8)
    included_pixels = np.ones(zones.shape, dtype=bool)

    counts = count_values_by_zone(zones, values, included_pixels)

    assert counts == {(0, 0): 1, (300, categories[1]): 2}


def test_count_values_by_zone_accumulates_windows_with_different_category_maxima():
    zones = np.array([[10, 10, 20], [10, 20, 20]], dtype=np.int32)
    values = np.array([[1, 2, 2], [1, 2, 3]], dtype=np.uint8)
    counts = Counter()

    for row in range(2):
        included_pixels = np.ones(zones[row].shape, dtype=bool)
        counts.update(count_values_by_zone(zones[row], values[row], included_pixels))

    assert counts == {(10, 1): 2, (10, 2): 1, (20, 2): 2, (20, 3): 1}


def test_iter_aligned_raster_windows_reads_matching_chunks():
    first = create_raster(np.arange(12).reshape(3, 4))
    second = create_raster(np.arange(12, 24).reshape(3, 4))
    third = create_raster(np.arange(24, 36).reshape(3, 4))

    windows = list(iter_aligned_raster_windows(first, second, third, window_size=2))

    assert [(window.width, window.height) for window in windows] == [
        (2, 2),
        (2, 2),
        (2, 1),
        (2, 1),
    ]
    np.testing.assert_array_equal(windows[-1].arrays[1], [[22, 23]])
    np.testing.assert_array_equal(windows[-1].arrays[2], [[34, 35]])


def test_iter_aligned_raster_windows_rejects_grid_difference():
    reference = create_raster(np.ones((2, 2)))
    shifted = create_raster(np.ones((2, 2)), geotransform=(1, 10, 0, 20, 0, -10))

    with pytest.raises(ValueError, match="does not match"):
        list(iter_aligned_raster_windows(reference, shifted))


def test_iter_aligned_raster_windows_rejects_rotation_difference():
    reference = create_raster(np.ones((2, 2)))
    rotated = create_raster(np.ones((2, 2)), geotransform=(0, 10, 1, 20, 0, -10))

    with pytest.raises(ValueError, match="does not match"):
        list(iter_aligned_raster_windows(reference, rotated))
