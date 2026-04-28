"""Tests for Environment Canada filename parsing"""

import logging

import pytest
from weather_model_jobs.env_canada import parse_env_canada_filename, parse_rdps_msc_filename
from wps_shared.weather_models import ModelEnum, ProjectionEnum

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "filename,projection,variable_name",
    [
        ("CMC_glb_TMP_TGL_2_latlon.24x.24_2020070212_P240.grib2", "latlon.24x.24", "TMP_TGL_2"),
        (
            "CMC_glb_ABSV_ISBL_200_latlon.24x.24_2020070600_P000.grib2",
            "latlon.24x.24",
            "ABSV_ISBL_200",
        ),
        (
            "CMC_glb_ABSV_ISBL_200_latlon.15x.15_2020070600_P000.grib2",
            "latlon.15x.15",
            "ABSV_ISBL_200",
        ),
        ("CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2", "latlon.15x.15", "RH_TGL_2"),
        (
            "/somewhere_on/the_drive/CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2",
            "latlon.15x.15",
            "RH_TGL_2",
        ),
    ],
)
def test_parse_filename(filename, projection, variable_name):
    """
    _summary_

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
        # Legacy CMC_reg format — still routed through parse_gdps_rdps_filename
        (
            "CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.REGIONAL_PS,
            "RH_TGL_2",
        ),
        (
            "CMC_reg_TMP_TGL_2_ps10km_2024010100_P003.grib2",
            ModelEnum.RDPS,
            ProjectionEnum.REGIONAL_PS,
            "TMP_TGL_2",
        ),
    ],
)
def test_parse_env_canada_filename_dispatches_rdps_urls(url, expected_model, expected_projection, expected_variable):
    info = parse_env_canada_filename(url)
    assert info.model_enum == expected_model
    assert info.projection == expected_projection
    assert info.variable_name == expected_variable
