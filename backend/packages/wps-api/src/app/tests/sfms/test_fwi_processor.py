import logging
import math
from dataclasses import dataclass
from unittest.mock import patch

import numpy as np
import pytest
from cffdrs import bui, dc, dmc, ffmc, fwi, isi
from osgeo import osr

from wps_shared.geospatial.wps_dataset import WPSDataset
from app.sfms.fwi_processor import check_weather_values, calculate_bui, calculate_dc, calculate_dmc, calculate_ffmc, calculate_fwi, calculate_isi


FWI_ARRAY = np.array([[12, 20], [-999, -999]])
WEATHER_ARRAY = np.array([[12, 20], [0, 0]])


@dataclass
class InputDatasets:
    bui: WPSDataset
    dc: WPSDataset
    dmc: WPSDataset
    ffmc: WPSDataset
    isi: WPSDataset
    temp: WPSDataset
    rh: WPSDataset
    precip: WPSDataset
    wind_speed: WPSDataset


@pytest.fixture
def input_datasets():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    transform = (-2, 1, 0, 2, 0, -1)

    return InputDatasets(
        bui=WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999),
        dc=WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999),
        dmc=WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999),
        ffmc=WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999),
        isi=WPSDataset.from_array(FWI_ARRAY, transform, srs.ExportToWkt(), nodata_value=-999),
        temp=WPSDataset.from_array(WEATHER_ARRAY, transform, srs.ExportToWkt()),
        rh=WPSDataset.from_array(WEATHER_ARRAY, transform, srs.ExportToWkt()),
        precip=WPSDataset.from_array(WEATHER_ARRAY, transform, srs.ExportToWkt()),
        wind_speed=WPSDataset.from_array(WEATHER_ARRAY, transform, srs.ExportToWkt()),
    )


@pytest.fixture
def latitude_month():
    latitude = np.array([[45, 45], [60, 60]])
    month = np.array([[6, 6], [7, 7]])
    return latitude, month


def test_calculate_dc_masked_correctly(input_datasets, latitude_month):
    dc_ds = input_datasets.dc
    temp_ds = input_datasets.temp
    rh_ds = input_datasets.rh
    precip_ds = input_datasets.precip
    latitude, month = latitude_month

    dc_values, nodata_value = calculate_dc(dc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dc_values.shape == (2, 2)
    assert dc_values[1, 0] == nodata_value
    assert dc_values[1, 1] == nodata_value
    assert dc_values[0, 0] != nodata_value
    assert dc_values[0, 1] != nodata_value


def test_calculate_dmc_masked_correctly(input_datasets, latitude_month):
    dmc_ds = input_datasets.dmc
    temp_ds = input_datasets.temp
    rh_ds = input_datasets.rh
    precip_ds = input_datasets.precip
    latitude, month = latitude_month

    dmc_values, nodata_value = calculate_dmc(dmc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    # validate output shape and nodata masking
    assert dmc_values.shape == (2, 2)
    assert dmc_values[1, 0] == nodata_value
    assert dmc_values[1, 1] == nodata_value
    assert dmc_values[0, 0] != nodata_value
    assert dmc_values[0, 1] != nodata_value


def test_calculate_bui_masked_correctly(input_datasets):
    dc_ds = input_datasets.dc
    dmc_ds = input_datasets.dmc

    bui_values, nodata_value = calculate_bui(dmc_ds, dc_ds)

    # validate output shape and nodata masking
    assert bui_values.shape == (2, 2)
    assert bui_values[1, 0] == nodata_value
    assert bui_values[1, 1] == nodata_value
    assert bui_values[0, 0] != nodata_value
    assert bui_values[0, 1] != nodata_value


def test_calculate_dmc_values(input_datasets, latitude_month):
    dmc_ds = input_datasets.dmc
    temp_ds = input_datasets.temp
    rh_ds = input_datasets.rh
    precip_ds = input_datasets.precip
    latitude, month = latitude_month

    dmc_sample = FWI_ARRAY[0, 0]
    temp_sample = WEATHER_ARRAY[0, 0]
    rh_sample = WEATHER_ARRAY[0, 0]
    precip_sample = WEATHER_ARRAY[0, 0]
    lat_sample = latitude[0, 0]
    month_sample = int(month[0, 0])

    dmc_values, _ = calculate_dmc(dmc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    static_dmc = dmc(dmc_sample, temp_sample, rh_sample, precip_sample, lat_sample, month_sample)

    assert math.isclose(static_dmc, dmc_values[0, 0], abs_tol=0.01)


def test_calculate_dc_values(input_datasets, latitude_month):
    dc_ds = input_datasets.dc
    temp_ds = input_datasets.temp
    rh_ds = input_datasets.rh
    precip_ds = input_datasets.precip
    latitude, month = latitude_month

    dc_sample = FWI_ARRAY[0, 0]
    temp_sample = WEATHER_ARRAY[0, 0]
    rh_sample = WEATHER_ARRAY[0, 0]
    precip_sample = WEATHER_ARRAY[0, 0]
    lat_sample = latitude[0, 0]
    month_sample = int(month[0, 0])

    dc_values, _ = calculate_dc(dc_ds, temp_ds, rh_ds, precip_ds, latitude, month)

    static_dmc = dc(dc_sample, temp_sample, rh_sample, precip_sample, lat_sample, month_sample)

    assert math.isclose(static_dmc, dc_values[0, 0], abs_tol=0.01)


def test_calculate_bui_values(input_datasets):
    dc_ds = input_datasets.dc
    dmc_ds = input_datasets.dmc

    dc_sample = FWI_ARRAY[0, 0]
    dmc_sample = FWI_ARRAY[0, 0]

    bui_values, _ = calculate_bui(dc_ds, dmc_ds)

    static_bui = bui(dmc_sample, dc_sample)

    assert math.isclose(static_bui, bui_values[0, 0], abs_tol=0.01)


def test_calculate_isi_masked_correctly(input_datasets):
    ffmc_ds = input_datasets.ffmc
    windspeed_ds = input_datasets.wind_speed

    isi_values, nodata_value = calculate_isi(ffmc_ds, windspeed_ds)

    # validate output shape and nodata masking
    assert isi_values.shape == (2, 2)
    assert isi_values[1, 0] == nodata_value
    assert isi_values[1, 1] == nodata_value
    assert isi_values[0, 0] != nodata_value
    assert isi_values[0, 1] != nodata_value


def test_calculate_isi_values(input_datasets):
    ffmc_ds = input_datasets.ffmc
    wind_speed_ds = input_datasets.wind_speed

    ffmc_sample = FWI_ARRAY[0, 0]
    wind_sample = WEATHER_ARRAY[0, 0]

    isi_values, _ = calculate_isi(ffmc_ds, wind_speed_ds)

    static_isi = isi(ffmc_sample, wind_sample)

    assert math.isclose(static_isi, isi_values[0, 0], abs_tol=0.01)


def test_calculate_ffmc_values(input_datasets):
    previous_ffmc_wps = input_datasets.ffmc
    temp_wps = input_datasets.temp
    rh_wps = input_datasets.rh
    precip_wps = input_datasets.precip
    wind_speed_wps = input_datasets.wind_speed

    previous_ffmc_sample = temp_sample = rh_sample = precip_sample = wind_speed_sample = FWI_ARRAY[0, 0]

    daily_ffmc_values, _ = calculate_ffmc(previous_ffmc_wps, temp_wps, rh_wps, precip_wps, wind_speed_wps)

    static_ffmc = ffmc(previous_ffmc_sample, temp_sample, rh_sample, wind_speed_sample, precip_sample)

    assert math.isclose(static_ffmc, daily_ffmc_values[0, 0], abs_tol=0.01)


def test_calculate_ffmc_masked_correctly(input_datasets):
    previous_ffmc_wps = input_datasets.ffmc
    temp_wps = input_datasets.temp
    rh_wps = input_datasets.rh
    precip_wps = input_datasets.precip
    wind_speed_wps = input_datasets.wind_speed

    daily_ffmc_values, nodata_value = calculate_ffmc(previous_ffmc_wps, temp_wps, rh_wps, precip_wps, wind_speed_wps)

    # validate output shape and nodata masking
    assert daily_ffmc_values.shape == (2, 2)
    assert daily_ffmc_values[1, 0] == nodata_value
    assert daily_ffmc_values[1, 1] == nodata_value
    assert daily_ffmc_values[0, 0] != nodata_value
    assert daily_ffmc_values[0, 1] != nodata_value


def test_calculate_fwi_masked_correctly(input_datasets):
    isi_ds = input_datasets.isi
    bui_ds = input_datasets.bui

    fwi_values, nodata_value = calculate_fwi(isi_ds, bui_ds)

    # validate output shape and nodata masking
    assert fwi_values.shape == (2, 2)
    assert fwi_values[1, 0] == nodata_value
    assert fwi_values[1, 1] == nodata_value
    assert fwi_values[0, 0] != nodata_value
    assert fwi_values[0, 1] != nodata_value


def test_calculate_fwi_values(input_datasets):
    isi_ds = input_datasets.isi
    bui_ds = input_datasets.bui

    isi_sample = FWI_ARRAY[0, 0]
    bui_sample = FWI_ARRAY[0, 0]

    fwi_values, _ = calculate_fwi(isi_ds, bui_ds)

    static_fwi = fwi(isi_sample, bui_sample)

    assert math.isclose(static_fwi, fwi_values[0, 0], abs_tol=0.01)


@pytest.mark.parametrize(
    "rh_array, expected",
    [
        (np.array([50, 60, 70]), False),
        (np.array([-5, 50, 110]), True),
    ],
)
def test_check_rh_logging(rh_array, expected):
    with patch("app.sfms.fwi_processor.logger") as mock_logger:
        check_weather_values(rh_array=rh_array)
        if expected:
            mock_logger.error.assert_called_once()
            assert "Relative humidity" in mock_logger.error.call_args[0][0]
        else:
            mock_logger.error.assert_not_called()


@pytest.mark.parametrize(
    "precip_array, expected",
    [
        (np.array([0.0, 5.0, 10.0]), False),
        (np.array([-1.0, 0.0, 2.0]), True),
    ],
)
def test_check_prec_logging(precip_array, expected):
    with patch("app.sfms.fwi_processor.logger") as mock_logger:
        check_weather_values(precip_array=precip_array)
        if expected:
            mock_logger.error.assert_called_once()
            assert "Precipitation" in mock_logger.error.call_args[0][0]
        else:
            mock_logger.error.assert_not_called()


@pytest.mark.parametrize(
    "ws_array, expected",
    [
        (np.array([0.0, 3.2, 7.5]), False),
        (np.array([-0.1, 1.0, 2.0]), True),
    ],
)
def test_check_ws_logging(ws_array, expected):
    with patch("app.sfms.fwi_processor.logger") as mock_logger:
        check_weather_values(ws_array=ws_array)
        if expected:
            mock_logger.error.assert_called_once()
            assert "Wind speed" in mock_logger.error.call_args[0][0]
        else:
            mock_logger.error.assert_not_called()


def test_check_multiple_issues():
    rh_array = np.array([-10, 105])
    precip_array = np.array([-2.5])
    ws_array = np.array([-1.0])

    with patch("app.sfms.fwi_processor.logger") as mock_logger:
        check_weather_values(rh_array=rh_array, precip_array=precip_array, ws_array=ws_array)

        error_calls = [call.args[0] for call in mock_logger.error.call_args_list]

        assert any("Relative humidity values out of bounds" in msg for msg in error_calls)
        assert any("Precipitation contains negative values" in msg for msg in error_calls)
        assert any("Wind speed contains negative values" in msg for msg in error_calls)

        assert mock_logger.error.call_count == 3
