from datetime import date
from unittest.mock import AsyncMock, MagicMock
import numpy as np
import pytest
from app.auto_spatial_advisory.hfi_percent_conifer import (
    get_minimum_percent_conifer_for_hfi,
    get_percent_conifer_s3_key,
    update_minimum_percent_conifer_by_zone,
)


def test_valid_values():
    pct_conifer_array = np.array([10, 20, 30, 40, 50])
    hfi_array = np.array([1000, 5000, 3000, 6000, 7000])
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) == 20


def test_no_valid_values():
    pct_conifer_array = np.array([10, 20, 30, 40, 50])
    hfi_array = np.array([1000, 2000, 3000, 1000, 500])  # No values > 4000
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) is None


def test_all_zeros():
    pct_conifer_array = np.array([0, 0, 0, 0, 0])
    hfi_array = np.array([5000, 5000, 5000, 5000, 5000])
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) is None


def test_some_zeros():
    pct_conifer_array = np.array([0, 20, 0, 40, 50])
    hfi_array = np.array([1000, 5000, 3000, 6000, 7000])
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) == 20


def test_nan_values():
    pct_conifer_array = np.array([np.nan, 20, 30, np.nan, 50])
    hfi_array = np.array([1000, 5000, 3000, 6000, 7000])
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) == 20


def test_no_values_above_threshold():
    pct_conifer_array = np.array([10, 20, 30])
    hfi_array = np.array([3000, 3500, 2000])  # All values below 4000
    assert get_minimum_percent_conifer_for_hfi(pct_conifer_array, hfi_array) is None


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
