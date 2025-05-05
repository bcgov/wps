import numpy as np
from wps_shared.db.crud.auto_spatial_advisory import HfiClassificationThresholdEnum

from app.auto_spatial_advisory.hfi_minimum_wind_speed import get_minimum_wind_speed_for_hfi

mock_advisory_id_lut = {HfiClassificationThresholdEnum.ADVISORY.value: 1, HfiClassificationThresholdEnum.WARNING.value: 2}


def test_minimum_wind_speed_for_hfi_normal_case():
    wind_speed_array = np.array([5, 10, 15, 20, 25])
    hfi_array = np.array([1000, 5000, 12000, 8000, 15000])

    result = get_minimum_wind_speed_for_hfi(wind_speed_array, hfi_array, mock_advisory_id_lut, -1)

    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]] == 10  # Smallest wind speed where HFI is 4000-9999
    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]] == 15  # Smallest wind speed where HFI is >= 10000


def test_no_matching_hfi_values():
    wind_speed_array = np.array([5, 10, 15, 20, 25])
    hfi_array = np.array([1000, 2000, 3000, 3500, 3800])  # All values below 4000

    result = get_minimum_wind_speed_for_hfi(wind_speed_array, hfi_array, mock_advisory_id_lut, -1)

    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]] is None
    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]] is None


def test_hfi_values_with_nan():
    wind_speed_array = np.array([5, 10, np.nan, 20, 25])
    hfi_array = np.array([1000, 5000, 12000, 8000, 15000])

    result = get_minimum_wind_speed_for_hfi(wind_speed_array, hfi_array, mock_advisory_id_lut, -1)

    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]] == 10  # min wind speed should be 10
    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]] == 25  # Ignore NaN, min wind speed should be 20


def test_empty_arrays():
    wind_speed_array = np.array([])
    hfi_array = np.array([])

    result = get_minimum_wind_speed_for_hfi(wind_speed_array, hfi_array, mock_advisory_id_lut, -1)

    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]] is None
    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]] is None


def test_arrays_with_no_data_values():
    wind_speed_array = np.array([12, -1, 14, 15])
    hfi_array = np.array([1000, 5000, 12000, 8000])

    result = get_minimum_wind_speed_for_hfi(wind_speed_array, hfi_array, mock_advisory_id_lut, -1)

    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]] == 15
    assert result[mock_advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]] == 14
