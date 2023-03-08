import pytest
import os
from osgeo import gdal
from datetime import datetime, timezone
import requests

from app.weather_models import process_grib
from app.weather_models import ModelEnum, ProjectionEnum
from app.jobs import noaa
from app.tests.weather_models.test_models_common import MockResponse


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
