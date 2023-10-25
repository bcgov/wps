import os
from osgeo import gdal
from pyproj import CRS
import math
from app.geospatial import NAD83_CRS
from app.stations import StationSourceEnum
from app.weather_models import process_grib


sample_values_json = [{
    'u_float': -3.711,
    'v_float': -1.471,
    'expected_wind_speed': 3.99,
    'expected_wind_direction': 22
},
    {
    'u_float': 2.93,
    'v_float': 4.06,
    'expected_wind_speed': 5.01,
    'expected_wind_direction': 234
},
    {
    'u_float': -1.77,
    'v_float': 1.95,
    'expected_wind_speed': 2.63,
    'expected_wind_direction': 312
},
    {
    'u_float': 6.04,
    'v_float': -0.31,
    'expected_wind_speed': 6.05,
    'expected_wind_direction': 177
}
]


def test_calculate_wind_speed_from_uv():
    for test_case in sample_values_json:
        calculated_wind_speed = process_grib.calculate_wind_speed_from_u_v(test_case['u_float'], test_case['v_float'])
        assert round(calculated_wind_speed, 2) == test_case['expected_wind_speed']


def test_calculate_wind_direction_from_uv():
    for test_case in sample_values_json:
        calculated_wind_direction = process_grib.calculate_wind_dir_from_u_v(
            test_case['u_float'], test_case['v_float'])
        assert round(calculated_wind_direction, 0) == test_case['expected_wind_direction']


def test_convert_mps_to_kph():
    metres_per_second_speed = 1
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert kilometres_per_hour_speed == 3.6  # 1m/s * 3600 sec/hour / 1000m/km


def test_convert_mps_to_kph_zero_wind_speed():
    metres_per_second_speed = 0
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert kilometres_per_hour_speed == 0


def test_read_single_raster_value():
    """
    Verified with gdallocationinfo CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2 -wgs84 -120.4816667 50.6733333
    """
    filename = os.path.join(os.path.dirname(__file__), 'CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2')
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
    # (this step is included because HRDPS grib files are in another coordinate system)
    wkt = dataset.GetProjection()
    crs = CRS.from_string(wkt)
    raster_to_geo_transformer = process_grib.get_transformer(crs, NAD83_CRS)
    geo_to_raster_transformer = process_grib.get_transformer(NAD83_CRS, crs)
    padf_transform = process_grib.get_dataset_geometry(filename)

    processor = process_grib.GribFileProcessor(StationSourceEnum.UNSPECIFIED,
                                               padf_transform,
                                               raster_to_geo_transformer,
                                               geo_to_raster_transformer)

    raster_band = dataset.GetRasterBand(1)
    station, value = next(processor.yield_value_for_stations(raster_band))

    assert math.isclose(value, 55.976, abs_tol=0.001)
    assert station.code == 322

    del dataset
