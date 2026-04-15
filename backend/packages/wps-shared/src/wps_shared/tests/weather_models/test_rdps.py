import datetime

from wps_shared.weather_models import ProjectionEnum
from wps_shared.weather_models.rdps import (
    RDPS_GRIB_LAYERS,
    SFMS_GRIB_LAYERS,
    get_regional_model_run_download_urls,
    parse_rdps_msc_filename,
)


def test_rdps_latlon_projection_exists():
    assert ProjectionEnum.RDPS_LATLON == "RLatLon0.09"


def test_rdps_grib_layers_use_new_variable_names():
    assert "TMP_AGL-2m" in RDPS_GRIB_LAYERS
    assert "RH_AGL-2m" in RDPS_GRIB_LAYERS
    assert "APCP_Sfc" in RDPS_GRIB_LAYERS
    assert "WDIR_AGL-10m" in RDPS_GRIB_LAYERS
    assert "WIND_AGL-10m" in RDPS_GRIB_LAYERS
    # old names must be gone
    assert "TMP_TGL_2" not in RDPS_GRIB_LAYERS
    assert "APCP_SFC_0" not in RDPS_GRIB_LAYERS


def test_sfms_grib_layers_use_new_variable_names():
    assert SFMS_GRIB_LAYERS["temp"] == "TMP_AGL-2m"
    assert SFMS_GRIB_LAYERS["rh"] == "RH_AGL-2m"
    assert SFMS_GRIB_LAYERS["precip"] == "APCP_Sfc"
    assert SFMS_GRIB_LAYERS["wind_speed"] == "WIND_AGL-10m"


def test_get_regional_model_run_download_urls_uses_new_path():
    now = datetime.datetime(2026, 5, 1, 12, tzinfo=datetime.timezone.utc)
    urls = list(get_regional_model_run_download_urls(now, 12))
    assert all("model_rdps" in u for u in urls)
    assert all("model_gem_regional" not in u for u in urls)
    assert all("MSC_RDPS" in u for u in urls)
    assert all("RLatLon0.09" in u for u in urls)


def test_get_regional_model_run_download_urls_skips_precip_at_hour_zero():
    now = datetime.datetime(2026, 5, 1, 12, tzinfo=datetime.timezone.utc)
    urls = list(get_regional_model_run_download_urls(now, 12))
    hour_zero_urls = [u for u in urls if "PT000H" in u]
    assert all("APCP_Sfc" not in u for u in hour_zero_urls)


def test_get_regional_model_run_download_urls_count():
    now = datetime.datetime(2026, 5, 1, 12, tzinfo=datetime.timezone.utc)
    # 85 hours * 5 layers - 1 (no precip at hour 0) = 424
    assert len(list(get_regional_model_run_download_urls(now, 12))) == 424


def test_parse_rdps_msc_filename_extracts_metadata():
    url = (
        "https://dd.weather.gc.ca/today/model_rdps/10km/12/003/"
        "20260501T12Z_MSC_RDPS_TMP_AGL-2m_RLatLon0.09_PT003H.grib2"
    )
    variable, projection, model_run_ts, prediction_ts = parse_rdps_msc_filename(url)
    assert variable == "TMP_AGL-2m"
    assert projection == ProjectionEnum.RDPS_LATLON
    assert model_run_ts.year == 2026
    assert model_run_ts.hour == 12
    assert prediction_ts.hour == 15  # 12 + 3


def test_parse_rdps_msc_filename_malformed_raises():
    import pytest

    with pytest.raises(Exception):
        parse_rdps_msc_filename("https://dd.weather.gc.ca/not-a-real-rdps-url/file.grib2")
