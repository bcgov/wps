import numpy as np

from app.auto_spatial_advisory.hfi_minimum_wind_speed import (
    ADVISORY_NAME,
    WARNING_NAME,
    update_minimum_wind_by_zone,
)


def test_update_minimum_wind_by_zone_groups_thresholds_and_ignores_nodata():
    minimums = {}

    update_minimum_wind_by_zone(
        minimums,
        zones=np.array([[1, 1, 2], [1, 2, -1]]),
        raw_hfi=np.array([[5000, 11000, 9000], [3000, 12000, 12000]]),
        wind_speed=np.array([[10.0, 12.0, 8.0], [4.0, -9999.0, 1.0]]),
        zone_nodata=-1,
        wind_nodata=-9999,
    )

    assert minimums == {
        (1, ADVISORY_NAME): 10,
        (2, ADVISORY_NAME): 8,
        (1, WARNING_NAME): 12,
    }


def test_update_minimum_wind_by_zone_ignores_nonfinite_values_without_nodata():
    minimums = {}

    update_minimum_wind_by_zone(
        minimums,
        zones=np.array([[1, 1], [2, 2]]),
        raw_hfi=np.array([[5000, 12000], [5000, 12000]]),
        wind_speed=np.array([[np.nan, np.inf], [7.0, 8.0]]),
        zone_nodata=-1,
        wind_nodata=None,
    )

    assert minimums == {
        (2, ADVISORY_NAME): 7,
        (2, WARNING_NAME): 8,
    }


def test_update_minimum_wind_by_zone_merges_minimums_across_windows():
    minimums = {}

    update_minimum_wind_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 12000]]),
        wind_speed=np.array([[10.0, 12.0]]),
        zone_nodata=-1,
        wind_nodata=None,
    )
    update_minimum_wind_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 12000]]),
        wind_speed=np.array([[8.0, 14.0]]),
        zone_nodata=-1,
        wind_nodata=None,
    )

    assert minimums == {
        (1, ADVISORY_NAME): 8,
        (2, WARNING_NAME): 12,
    }


def test_update_minimum_wind_by_zone_leaves_empty_results_unchanged():
    minimums = {}

    update_minimum_wind_by_zone(
        minimums,
        zones=np.array([[-1, -1]]),
        raw_hfi=np.array([[1000, 2000]]),
        wind_speed=np.array([[5.0, 6.0]]),
        zone_nodata=-1,
        wind_nodata=None,
    )

    assert minimums == {}
