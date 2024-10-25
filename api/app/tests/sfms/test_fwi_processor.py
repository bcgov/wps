import pytest
import numpy as np
from unittest.mock import MagicMock
from app.geospatial.wps_dataset import WPSDataset
from app.sfms.fwi_processor import calculate_dc, calculate_dmc, calculate_bui


@pytest.fixture
def sample_datasets():
    # Create mock datasets with MagicMock for replace_nodata_with and get_nodata_mask
    dc_ds = MagicMock(spec=WPSDataset)
    dmc_ds = MagicMock(spec=WPSDataset)
    temp_ds = MagicMock(spec=WPSDataset)
    rh_ds = MagicMock(spec=WPSDataset)
    precip_ds = MagicMock(spec=WPSDataset)

    # Mock NoData replacement
    dc_ds.replace_nodata_with.return_value = (np.array([[1, 2], [0, 0]]), 0)
    dmc_ds.replace_nodata_with.return_value = (np.array([[3, 4], [0, 0]]), 0)
    temp_ds.replace_nodata_with.return_value = (np.array([[10, 15], [0, 0]]), 0)
    rh_ds.replace_nodata_with.return_value = (np.array([[50, 55], [0, 0]]), 0)
    precip_ds.replace_nodata_with.return_value = (np.array([[1, 0], [0, 2]]), 0)

    # Mock NoData mask
    dc_ds.get_nodata_mask.return_value = (np.array([[False, False], [True, True]]), -9999)
    dmc_ds.get_nodata_mask.return_value = (np.array([[False, False], [True, True]]), -9999)

    return dc_ds, dmc_ds, temp_ds, rh_ds, precip_ds


@pytest.fixture
def latitude_month():
    latitude = np.array([[45, 45], [60, 60]])
    month = np.array([[6, 6], [7, 7]])
    return latitude, month


def test_calculate_dc(sample_datasets, latitude_month):
    dc_ds, _, temp_ds, rh_ds, precip_ds = sample_datasets
    latitude, month = latitude_month

    dc_values, nodata_value = calculate_dc(dc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dc_values.shape == (2, 2)
    assert dc_values[1, 0] == nodata_value
    assert dc_values[1, 1] == nodata_value
    assert dc_values[0, 0] != nodata_value
    assert dc_values[0, 1] != nodata_value


def test_calculate_dmc(sample_datasets, latitude_month):
    _, dmc_ds, temp_ds, rh_ds, precip_ds = sample_datasets
    latitude, month = latitude_month

    dmc_values, nodata_value = calculate_dmc(dmc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dmc_values.shape == (2, 2)
    assert dmc_values[1, 0] == nodata_value
    assert dmc_values[1, 1] == nodata_value
    assert dmc_values[0, 0] != nodata_value
    assert dmc_values[0, 1] != nodata_value


def test_calculate_bui(sample_datasets):
    dc_ds, dmc_ds, _, _, _ = sample_datasets

    bui_values, nodata_value = calculate_bui(dmc_ds, dc_ds)

    # validate output shape and nodata masking
    assert bui_values.shape == (2, 2)
    assert bui_values[1, 0] == nodata_value
    assert bui_values[1, 1] == nodata_value
    assert bui_values[0, 0] != nodata_value
    assert bui_values[0, 1] != nodata_value
