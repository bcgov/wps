from datetime import date
from unittest.mock import AsyncMock, MagicMock
import numpy as np
import pytest
from app.auto_spatial_advisory.hfi_percent_conifer import (
    get_percent_conifer_s3_key,
    update_minimum_percent_conifer_by_zone,
)


def test_update_minimum_percent_conifer_by_zone_groups_valid_pixels():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 1, 2], [1, 2, -1]]),
        raw_hfi=np.array([[5000, 11000, 9000], [3000, 12000, 12000]]),
        percent_conifer=np.array([[30.0, 20.0, 15.0], [10.0, 0.0, 5.0]]),
        zone_nodata=-1,
    )

    assert minimums == {1: 20, 2: 15}


def test_update_minimum_percent_conifer_by_zone_ignores_invalid_values_and_hfi_boundary():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 1, 2, 2]]),
        raw_hfi=np.array([[4000, 4001, 5000, 5000]]),
        percent_conifer=np.array([[50.0, np.nan, np.inf, 25.0]]),
        zone_nodata=-1,
    )

    assert minimums == {2: 25}


def test_update_minimum_percent_conifer_by_zone_merges_minimums_across_windows():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 5000]]),
        percent_conifer=np.array([[30.0, 40.0]]),
        zone_nodata=-1,
    )
    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 5000]]),
        percent_conifer=np.array([[20.0, 50.0]]),
        zone_nodata=-1,
    )

    assert minimums == {1: 20, 2: 40}


def test_update_minimum_percent_conifer_by_zone_leaves_empty_results_unchanged():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[-1, -1]]),
        raw_hfi=np.array([[4000, 3000]]),
        percent_conifer=np.array([[20.0, 30.0]]),
        zone_nodata=-1,
    )

    assert minimums == {}


@pytest.fixture
def mock_s3():
    mock = MagicMock()
    mock.bucket = "bucket"
    mock.all_objects_exist = AsyncMock()
    return mock


SFMS_TEST_DATE = date(2024, 12, 15)


@pytest.mark.anyio
async def test_get_percent_conifer_s3_key_current_year(mock_s3):
    mock_s3.all_objects_exist.side_effect = lambda key: "m12_2024.tif" in key

    key = await get_percent_conifer_s3_key(SFMS_TEST_DATE, mock_s3)
    assert key == "/vsis3/bucket/sfms/static/m12_2024.tif"


@pytest.mark.anyio
async def test_get_percent_conifer_s3_key_fallback_year(mock_s3):
    mock_s3.all_objects_exist.side_effect = lambda key: "m12_2023.tif" in key

    key = await get_percent_conifer_s3_key(SFMS_TEST_DATE, mock_s3)
    assert key == "/vsis3/bucket/sfms/static/m12_2023.tif"


@pytest.mark.anyio
async def test_get_percent_conifer_s3_key_none_exist(mock_s3):
    mock_s3.all_objects_exist.return_value = False

    key = await get_percent_conifer_s3_key(SFMS_TEST_DATE, mock_s3)
    assert key is None
