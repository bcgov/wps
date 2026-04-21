"""Unit tests for wps_shared/weather_models/model_run_urls.py"""

from datetime import datetime, timezone

import pytest

from wps_shared.weather_models import ModelEnum, UnhandledPredictionModelType, get_file_date_part
from wps_shared.weather_models.model_run_urls import (
    GDPS_GRIB_LAYERS,
    HRDPS_GRIB_LAYERS,
    RDPS_GRIB_LAYERS,
    get_global_model_run_download_urls,
    get_high_res_model_run_download_urls,
    get_model_run_urls,
    get_regional_model_run_download_urls,
)
from wps_shared.weather_models.rdps import RDPS_VARIABLE_NAMES

NOW = datetime(2026, 4, 21, 8, 0, 0, tzinfo=timezone.utc)


class TestGetRegionalModelRunDownloadUrls:
    def test_total_url_count(self):
        # 85 hours * n layers, minus 1 for the precip skip at hour 000
        urls = list(get_regional_model_run_download_urls(NOW, 0))
        assert len(urls) == 85 * len(RDPS_GRIB_LAYERS) - 1

    def test_precip_skipped_at_hour_000(self):
        urls = list(get_regional_model_run_download_urls(NOW, 0))
        precip_layer = RDPS_VARIABLE_NAMES["precip"]
        assert not any("PT000H" in u and precip_layer in u for u in urls)

    def test_url_format(self):
        date = get_file_date_part(NOW, 0)
        urls = list(get_regional_model_run_download_urls(NOW, 0))
        assert urls[0] == (
            f"https://dd.weather.gc.ca/today/model_rdps/10km/00/000/"
            f"{date}T00Z_MSC_RDPS_{RDPS_GRIB_LAYERS[0]}_RLatLon0.09_PT000H.grib2"
        )

    def test_model_run_hour_12(self):
        date = get_file_date_part(NOW, 12)
        urls = list(get_regional_model_run_download_urls(NOW, 12))
        assert all("model_rdps/10km/12/" in u for u in urls)
        assert any(f"{date}T12Z" in u for u in urls)

    def test_custom_grib_layers_and_limit(self):
        custom_layers = (RDPS_VARIABLE_NAMES["temp"],)
        urls = list(get_regional_model_run_download_urls(NOW, 0, grib_layers=custom_layers, limit=3))
        assert len(urls) == 3
        assert all(RDPS_VARIABLE_NAMES["temp"] in u for u in urls)


class TestGetGlobalModelRunDownloadUrls:
    def test_total_url_count(self):
        # 81 steps (0-240 in steps of 3) * n layers, minus 1 for the precip skip at 000
        urls = list(get_global_model_run_download_urls(NOW, 0))
        assert len(urls) == 81 * len(GDPS_GRIB_LAYERS) - 1

    def test_precip_skipped_at_hour_000(self):
        urls = list(get_global_model_run_download_urls(NOW, 0))
        assert not any("_P000.grib2" in u and "APCP_SFC_0" in u for u in urls)

    def test_url_format(self):
        date = get_file_date_part(NOW, 0)
        urls = list(get_global_model_run_download_urls(NOW, 0))
        assert urls[0].startswith("https://dd.weather.gc.ca/today/model_gem_global/15km/grib2/lat_lon/00/000/")
        assert f"CMC_glb_{GDPS_GRIB_LAYERS[0]}_latlon.15x.15_{date}00_P000.grib2" in urls[0]


class TestGetHighResModelRunDownloadUrls:
    def test_total_url_count(self):
        # 49 hours (0-48) * n layers, minus 1 for the precip skip at 000
        urls = list(get_high_res_model_run_download_urls(NOW, 0))
        assert len(urls) == 49 * len(HRDPS_GRIB_LAYERS) - 1

    def test_precip_skipped_at_hour_000(self):
        urls = list(get_high_res_model_run_download_urls(NOW, 0))
        assert not any("PT000H" in u and "APCP_Sfc" in u for u in urls)

    def test_url_format(self):
        date = get_file_date_part(NOW, 0, True)
        urls = list(get_high_res_model_run_download_urls(NOW, 0))
        assert urls[0].startswith("https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/00/000/")
        assert f"{date}_MSC_HRDPS_{HRDPS_GRIB_LAYERS[0]}_RLatLon0.0225_PT000H.grib2" in urls[0]


class TestGetModelRunUrls:
    def test_dispatches_gdps(self):
        urls = get_model_run_urls(NOW, ModelEnum.GDPS, 0)
        assert len(urls) == 81 * len(GDPS_GRIB_LAYERS) - 1

    def test_dispatches_rdps(self):
        urls = get_model_run_urls(NOW, ModelEnum.RDPS, 0)
        assert len(urls) == 85 * len(RDPS_GRIB_LAYERS) - 1

    def test_dispatches_hrdps(self):
        urls = get_model_run_urls(NOW, ModelEnum.HRDPS, 0)
        assert len(urls) == 49 * len(HRDPS_GRIB_LAYERS) - 1

    def test_raises_on_unknown_model(self):
        with pytest.raises(UnhandledPredictionModelType):
            get_model_run_urls(NOW, ModelEnum.GFS, 0)
