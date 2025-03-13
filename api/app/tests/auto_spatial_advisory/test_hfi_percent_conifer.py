import numpy as np
from app.auto_spatial_advisory.hfi_percent_conifer import get_minimum_percent_conifer_for_hfi


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
