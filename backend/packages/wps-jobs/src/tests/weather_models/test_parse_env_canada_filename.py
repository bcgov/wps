"""Tests for Environment Canada filename parsing"""

import logging

import pytest
from weather_model_jobs.env_canada import (
    parse_env_canada_filename,
    parse_gdps_msc_filename,
    parse_rdps_msc_filename,
)
from wps_shared.weather_models import ModelEnum, ProjectionEnum

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "filename,projection,variable_name",
    [
        (
            "20260501T12Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT003H.grib2",
            ProjectionEnum.LATLON_15X_15,
            "AirTemp_AGL-2m",
        ),
        (
            "20260501T00Z_MSC_GDPS_RelativeHumidity_AGL-2m_LatLon0.15_PT000H.grib2",
            ProjectionEnum.LATLON_15X_15,
            "RelativeHumidity_AGL-2m",
        ),
        (
            "20260501T12Z_MSC_GDPS_Precip-Accum_Sfc_LatLon0.15_PT006H.grib2",
            ProjectionEnum.LATLON_15X_15,
            "Precip-Accum_Sfc",
        ),
        (
            "/somewhere_on/the_drive/20260501T12Z_MSC_GDPS_WindSpeed_AGL-10m_LatLon0.15_PT003H.grib2",
            ProjectionEnum.LATLON_15X_15,
            "WindSpeed_AGL-10m",
        ),
    ],
)
def test_parse_filename(filename, projection, variable_name):
    """
    Parse current MSC GDPS filenames.

    :param filename: filename to parse
    :param projection: expected projection
    :param variable_name: expected weather variable
    """
    parsed_file = parse_env_canada_filename(filename)
    assert parsed_file.projection == projection
    assert parsed_file.variable_name == variable_name


def test_parse_rdps_msc_filename_extracts_metadata():
    url = (
        "https://dd.weather.gc.ca/today/model_rdps/10km/12/003/"
        "20260501T12Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2"
    )
    variable, projection, model_run_ts, prediction_ts = parse_rdps_msc_filename(url)
    assert variable == "AirTemp_AGL-2m"
    assert projection == ProjectionEnum.RDPS_LATLON
    assert model_run_ts.year == 2026
    assert model_run_ts.hour == 12
    assert prediction_ts.hour == 15  # 12 + 3


def test_parse_rdps_msc_filename_malformed_raises():
    with pytest.raises(ValueError):
        parse_rdps_msc_filename("https://dd.weather.gc.ca/not-a-real-rdps-url/file.grib2")


@pytest.mark.parametrize(
    "url,expected_model,expected_projection,expected_variable",
    [
        # New MSC format — routes via parse_rdps_msc_filename
        (
            "https://dd.weather.gc.ca/today/model_rdps/10km/00/003/"
            "20260501T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.RDPS_LATLON,
            "AirTemp_AGL-2m",
        ),
        (
            "https://dd.weather.gc.ca/today/model_rdps/10km/12/034/"
            "20260501T12Z_MSC_RDPS_WindSpeed_AGL-10m_RLatLon0.09_PT034H.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.RDPS_LATLON,
            "WindSpeed_AGL-10m",
        ),
        (
            "https://dd.weather.gc.ca/today/model_rdps/10km/00/034/"
            "20260501T00Z_MSC_RDPS_RelativeHumidity_AGL-2m_RLatLon0.09_PT034H.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.RDPS_LATLON,
            "RelativeHumidity_AGL-2m",
        ),
        (
            "https://dd.weather.gc.ca/today/model_rdps/10km/18/003/"
            "20260501T18Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.RDPS_LATLON,
            "AirTemp_AGL-2m",
        ),
    ],
)
def test_parse_env_canada_filename_dispatches_rdps_urls(
    url, expected_model, expected_projection, expected_variable
):
    info = parse_env_canada_filename(url)
    assert info.model_enum == expected_model
    assert info.projection == expected_projection
    assert info.variable_name == expected_variable


def test_parse_gdps_msc_filename_extracts_metadata():
    url = (
        "https://dd.weather.gc.ca/today/model_gdps/15km/12/003/"
        "20260501T12Z_MSC_GDPS_TMP_AGL-2m_LatLon0.15_PT003H.grib2"
    )

    variable, projection, model_run_ts, prediction_ts = parse_gdps_msc_filename(url)

    assert variable == "TMP_AGL-2m"
    assert projection == ProjectionEnum.LATLON_15X_15
    assert model_run_ts.year == 2026
    assert model_run_ts.month == 5
    assert model_run_ts.day == 1
    assert model_run_ts.hour == 12
    assert prediction_ts.hour == 15  # 12 + 3


def test_parse_gdps_msc_filename_malformed_raises():
    with pytest.raises(ValueError):
        parse_gdps_msc_filename("https://dd.weather.gc.ca/not-a-real-gdps-url/file.grib2")


def test_parse_gdps_msc_filename_prediction_timestamp_rolls_over_day():
    url = (
        "https://dd.weather.gc.ca/today/model_gdps/15km/12/015/"
        "20260501T12Z_MSC_GDPS_TMP_AGL-2m_LatLon0.15_PT015H.grib2"
    )

    variable, projection, model_run_ts, prediction_ts = parse_gdps_msc_filename(url)

    assert variable == "TMP_AGL-2m"
    assert projection == ProjectionEnum.LATLON_15X_15
    assert model_run_ts.day == 1
    assert model_run_ts.hour == 12
    assert prediction_ts.day == 2
    assert prediction_ts.hour == 3  # 12 + 15 = 03Z next day
