import math
import os

import pytest
from aiohttp import ClientSession
from osgeo import gdal
from pyproj import CRS
from weather_model_jobs.utils import process_grib
from wps_shared.geospatial.geospatial import NAD83_CRS
from wps_shared.tests.common import default_mock_client_get


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
