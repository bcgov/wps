from wps_shared.weather_models import ProjectionEnum
from wps_shared.weather_models.rdps import RDPS_VARIABLE_NAMES, parse_rdps_msc_filename


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
