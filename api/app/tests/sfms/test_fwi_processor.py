import math

import numpy as np
import pytest
from cffdrs import bui, dc, dmc, ffmc
from osgeo import osr

from app.geospatial.wps_dataset import WPSDataset
from app.sfms.fwi_processor import calculate_bui, calculate_dc, calculate_dmc, calculate_ffmc

FWI_ARRAY = np.array([[12, 20], [-999, -999]])
TEST_ARRAY = np.array([[12, 20], [0, 0]])


@pytest.fixture
def sample_bui_input_datasets():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    transform = (-2, 1, 0, 2, 0, -1)

    dc_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    dmc_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    temp_wps = WPSDataset.from_array(TEST_ARRAY, transform, srs.ExportToWkt())
    rh_wps = WPSDataset.from_array(TEST_ARRAY, transform, srs.ExportToWkt())
    precip_wps = WPSDataset.from_array(TEST_ARRAY, transform, srs.ExportToWkt())

    return dc_wps, dmc_wps, temp_wps, rh_wps, precip_wps


@pytest.fixture
def latitude_month():
    latitude = np.array([[45, 45], [60, 60]])
    month = np.array([[6, 6], [7, 7]])
    return latitude, month


@pytest.fixture
def sample_daily_ffmc_input_datasets():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    transform = (-2, 1, 0, 2, 0, -1)

    previous_ffmc_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    temp_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    rh_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    wind_speed_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)
    precip_wps = WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999)

    return previous_ffmc_wps, temp_wps, rh_wps, precip_wps, wind_speed_wps


def test_calculate_dc_masked_correctly(sample_bui_input_datasets, latitude_month):
    dc_ds, _, temp_ds, rh_ds, precip_ds = sample_bui_input_datasets
    latitude, month = latitude_month

    dc_values, nodata_value = calculate_dc(dc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dc_values.shape == (2, 2)
    assert dc_values[1, 0] == nodata_value
    assert dc_values[1, 1] == nodata_value
    assert dc_values[0, 0] != nodata_value
    assert dc_values[0, 1] != nodata_value


def test_calculate_dmc_masked_correctly(sample_bui_input_datasets, latitude_month):
    _, dmc_ds, temp_ds, rh_ds, precip_ds = sample_bui_input_datasets
    latitude, month = latitude_month

    dmc_values, nodata_value = calculate_dmc(dmc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dmc_values.shape == (2, 2)
    assert dmc_values[1, 0] == nodata_value
    assert dmc_values[1, 1] == nodata_value
    assert dmc_values[0, 0] != nodata_value
    assert dmc_values[0, 1] != nodata_value


def test_calculate_bui_masked_correctly(sample_bui_input_datasets):
    dc_ds, dmc_ds, _, _, _ = sample_bui_input_datasets

    bui_values, nodata_value = calculate_bui(dmc_ds, dc_ds)

    # validate output shape and nodata masking
    assert bui_values.shape == (2, 2)
    assert bui_values[1, 0] == nodata_value
    assert bui_values[1, 1] == nodata_value
    assert bui_values[0, 0] != nodata_value
    assert bui_values[0, 1] != nodata_value


def test_calculate_dmc_values(sample_bui_input_datasets, latitude_month):
    _, dmc_ds, temp_ds, rh_ds, precip_ds = sample_bui_input_datasets
    latitude, month = latitude_month

    dmc_sample = FWI_ARRAY[0, 0]
    temp_sample = TEST_ARRAY[0, 0]
    rh_sample = TEST_ARRAY[0, 0]
    precip_sample = TEST_ARRAY[0, 0]
    lat_sample = latitude[0, 0]
    month_sample = int(month[0, 0])

    dmc_values, _ = calculate_dmc(dmc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    static_dmc = dmc(dmc_sample, temp_sample, rh_sample, precip_sample, lat_sample, month_sample)

    assert math.isclose(static_dmc, dmc_values[0, 0], abs_tol=0.01)


def test_calculate_dc_values(sample_bui_input_datasets, latitude_month):
    dc_ds, _, temp_ds, rh_ds, precip_ds = sample_bui_input_datasets
    latitude, month = latitude_month

    dc_sample = FWI_ARRAY[0, 0]
    temp_sample = TEST_ARRAY[0, 0]
    rh_sample = TEST_ARRAY[0, 0]
    precip_sample = TEST_ARRAY[0, 0]
    lat_sample = latitude[0, 0]
    month_sample = int(month[0, 0])

    dc_values, _ = calculate_dc(dc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    static_dmc = dc(dc_sample, temp_sample, rh_sample, precip_sample, lat_sample, month_sample)

    assert math.isclose(static_dmc, dc_values[0, 0], abs_tol=0.01)


def test_calculate_bui_values(sample_bui_input_datasets):
    dc_ds, dmc_ds, *_ = sample_bui_input_datasets

    dc_sample = FWI_ARRAY[0, 0]
    dmc_sample = FWI_ARRAY[0, 0]

    bui_values, _ = calculate_bui(dc_ds, dmc_ds)

    static_bui = bui(dmc_sample, dc_sample)

    assert math.isclose(static_bui, bui_values[0, 0], abs_tol=0.01)


def test_calculate_daily_values(sample_daily_ffmc_input_datasets):
    previous_ffmc_wps, temp_wps, rh_wps, precip_wps, wind_speed_wps = sample_daily_ffmc_input_datasets

    previous_ffmc_sample = temp_sample = rh_sample = precip_sample = wind_speed_sample = FWI_ARRAY[0, 0]

    daily_ffmc_values, _ = calculate_ffmc(previous_ffmc_wps, temp_wps, rh_wps, precip_wps, wind_speed_wps)

    static_ffmc = ffmc(previous_ffmc_sample, temp_sample, rh_sample, wind_speed_sample, precip_sample)

    assert math.isclose(static_ffmc, daily_ffmc_values[0, 0], abs_tol=0.01)
