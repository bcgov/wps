import math
import os

import numpy as np
import pytest
from affine import Affine
from aiohttp import ClientSession
from osgeo import gdal
from pyproj import CRS
from weather_model_jobs.utils import process_grib
from wps_shared.geospatial.geospatial import NAD83_CRS
from wps_shared.schemas.stations import WeatherStation
from wps_shared.tests.common import default_mock_client_get
from wps_shared.weather_models import ModelEnum


def test_convert_mps_to_kph():
    metres_per_second_speed = 1
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert math.isclose(
        kilometres_per_hour_speed, 3.6, abs_tol=0.1
    )  # 1m/s * 3600 sec/hour / 1000m/km


def test_convert_mps_to_kph_zero_wind_speed():
    metres_per_second_speed = 0
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert kilometres_per_hour_speed == 0


@pytest.mark.parametrize(
    "variable_name,expected",
    [
        ("AirTemp_AGL-2m", "tmp_tgl_2"),
        ("RelativeHumidity_AGL-2m", "rh_tgl_2"),
        ("Precip-Accum_Sfc", "apcp_sfc_0"),
        ("WindSpeed_AGL-10m", "wind_tgl_10"),
        ("WindDir_AGL-10m", "wdir_tgl_10"),
        ("TMP_TGL_2", "tmp_tgl_2"),
    ],
)
def test_get_variable_name_maps_gdps_filename_variables(variable_name, expected):
    grib_info = process_grib.ModelRunInfo(
        model_enum=ModelEnum.GDPS,
        variable_name=variable_name,
    )
    processor = process_grib.GribFileProcessor.__new__(process_grib.GribFileProcessor)

    assert processor.get_variable_name(grib_info) == expected


def test_read_single_raster_value(monkeypatch: pytest.MonkeyPatch):
    """
    Verified with gdallocationinfo 20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2 -wgs84 -120.4816667 50.6733333
    """
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    filename = os.path.join(
        os.path.dirname(__file__), "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2"
    )
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
    # (this step is included because HRDPS grib files are in another coordinate system)
    wkt = dataset.GetProjection()
    crs = CRS.from_string(wkt)
    raster_to_geo_transformer = process_grib.get_transformer(crs, NAD83_CRS)
    geo_to_raster_transformer = process_grib.get_transformer(NAD83_CRS, crs)
    padf_transform = process_grib.get_dataset_transform(filename)

    processor = process_grib.GribFileProcessor(
        padf_transform, raster_to_geo_transformer, geo_to_raster_transformer
    )

    raster_band = dataset.GetRasterBand(1)
    station, value = next(processor.yield_value_for_stations(raster_band))

    assert station.code == 995
    assert math.isclose(value, 21.893, abs_tol=0.001)

    del dataset


@pytest.mark.parametrize("raw_value", [0.0, 21.125, -9999.0, float("nan"), float("inf")])
def test_weather_reader_skips_uncovered_stations_and_preserves_raw_values(
    raw_value: float, caplog: pytest.LogCaptureFixture
) -> None:
    with gdal.GetDriverByName("MEM").Create("", 1, 1, 1, gdal.GDT_Float32) as dataset:
        dataset.SetGeoTransform((-130.05, 0.1, 0, 51.05, 0, -0.1))
        band = dataset.GetRasterBand(1)
        band.SetNoDataValue(-9999)
        band.WriteArray(np.array([[raw_value]], dtype=np.float32))
        processor = process_grib.GribFileProcessor.__new__(process_grib.GribFileProcessor)
        processor.stations = [
            WeatherStation(code=1, name="Outside grid", lat=55, long=-130),
            WeatherStation(code=2, name="Covered", lat=51, long=-130),
        ]
        processor.padf_transform = Affine.from_gdal(*dataset.GetGeoTransform())
        processor.geo_to_raster_transformer = process_grib.get_transformer(NAD83_CRS, NAD83_CRS)

        values = list(processor.yield_value_for_stations(band))

    assert len(values) == 1
    station, value = values[0]
    assert station.code == 2
    assert isinstance(value, np.float32)
    if math.isnan(raw_value):
        assert math.isnan(value)
    else:
        assert value == raw_value
    assert "coordinate not in raster" in caplog.text
