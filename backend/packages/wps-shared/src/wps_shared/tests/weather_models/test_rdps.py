from datetime import datetime, timezone

import pytest

from wps_shared.weather_models import ProjectionEnum
from wps_shared.weather_models.rdps import RDPS_VARIABLE_NAMES, RDPSKeyAddresser


def test_rdps_latlon_projection_exists():
    assert ProjectionEnum.RDPS_LATLON == "RLatLon0.09"


def test_rdps_grib_layers_no_old_variable_names():
    assert "TMP_TGL-2m" not in RDPS_VARIABLE_NAMES.values()
    assert "RH_TGL-2m" not in RDPS_VARIABLE_NAMES.values()
    assert "APCP_SFC-0" not in RDPS_VARIABLE_NAMES.values()
    assert "WIND_TGL-10m" not in RDPS_VARIABLE_NAMES.values()
    assert "WDIR_TGL-10m" not in RDPS_VARIABLE_NAMES.values()


def test_sfms_grib_layers_use_new_variable_names():
    assert RDPS_VARIABLE_NAMES["temp"] == "AirTemp_AGL-2m"
    assert RDPS_VARIABLE_NAMES["rh"] == "RelativeHumidity_AGL-2m"
    assert RDPS_VARIABLE_NAMES["precip"] == "Precip-Accum_Sfc"
    assert RDPS_VARIABLE_NAMES["wind_speed"] == "WindSpeed_AGL-10m"
    assert RDPS_VARIABLE_NAMES["wind_dir"] == "WindDir_AGL-10m"


@pytest.mark.parametrize(
    "forecast_start_date,run_hour,forecast_hour,weather_parameter,expected_key",
    [
        (
            datetime(2023, 12, 31, 0, tzinfo=timezone.utc),
            0,
            3,
            "temp",
            "00/temp/CMC_reg_TMP_TGL_2_ps10km_2023123100_P003.grib2",
        ),
        (
            datetime(2023, 12, 31, 12, tzinfo=timezone.utc),
            12,
            15,
            "rh",
            "12/rh/CMC_reg_RH_TGL_2_ps10km_2023123112_P003.grib2",
        ),
        (
            datetime(2023, 12, 31, 0, tzinfo=timezone.utc),
            0,
            24,
            "precip",
            "00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P024.grib2",
        ),
    ],
)
def test_compose_rdps_key_legacy(forecast_start_date, run_hour, forecast_hour, weather_parameter, expected_key):
    result = RDPSKeyAddresser().compose_rdps_key_legacy(forecast_start_date, run_hour, forecast_hour, weather_parameter)
    assert result == expected_key


@pytest.mark.parametrize(
    "model_run_start,offset_hour,weather_parameter,expected_key",
    [
        (
            datetime(2024, 10, 10, 0, tzinfo=timezone.utc),
            3,
            "temp",
            "00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P003.grib2",
        ),
        (
            datetime(2024, 10, 10, 12, tzinfo=timezone.utc),
            6,
            "wind_speed",
            "12/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101012_P006.grib2",
        ),
    ],
)
def test_compose_rdps_key_hffmc_legacy(model_run_start, offset_hour, weather_parameter, expected_key):
    result = RDPSKeyAddresser().compose_rdps_key_hffmc_legacy(model_run_start, offset_hour, weather_parameter)
    assert result == expected_key
