import os
from datetime import datetime

import numpy as np
import pytest
from aiohttp import ClientSession
from herbie import Herbie
from osgeo import gdal
from pyproj import CRS

from app.geospatial import NAD83_CRS
from app.tests.common import default_mock_client_get
from app.weather_models import process_grib_herbie
from app.weather_models.process_grib import get_transformer
from app.weather_models.process_grib_herbie import TEMP, TEMP_FIELD, calculate_relative_humidity


@pytest.fixture
def mock_herbie_download_grib(monkeypatch):
    """fixture for herbie download and xarray"""
    dirname = os.path.dirname(os.path.realpath(__file__))
    grib_file = os.path.join(
        dirname, "ifs", "20250114", "subset_d5ef1aeb__20250114000000-0h-oper-fc.grib2"
    )

    def herbie_download(*args, **kwargs):
        return grib_file

    monkeypatch.setattr(Herbie, "download", herbie_download)


@pytest.fixture
def mock_herbie_find_grib(monkeypatch):
    """fixture for herbie download and xarray"""
    dirname = os.path.dirname(os.path.realpath(__file__))
    grib_file = os.path.join(
        dirname, "ifs", "20250114", "subset_d5ef1aeb__20250114000000-0h-oper-fc.grib2"
    )
    index_file = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20250114/00z/ifs/0p25/oper/20250114000000-0h-oper-fc.index"

    def herbie_find_grib(*args, **kwargs):
        return grib_file, "aws"

    def herbie_find_index(*args, **kwargs):
        return index_file, "aws"

    monkeypatch.setattr(Herbie, "find_grib", herbie_find_grib)
    monkeypatch.setattr(Herbie, "find_idx", herbie_find_index)


@pytest.mark.parametrize(
    "temp, dew_temp, expected",
    [
        (300.15, 293.15, 65.56),  # Normal case, temp and dew_temp in Kelvin
        (273.15, 273.15, 100.0),  # Saturated air (temp == dew_temp)
        (303.15, 283.15, 28.94),  # Higher temperature, lower dew_temp
        (250.15, 250.15, 100.0),  # Cold, saturated air
        (310.15, 280.15, 15.96),  # Hot and dry conditions
    ],
)
def test_calculate_relative_humidity(temp, dew_temp, expected):
    result = calculate_relative_humidity(temp, dew_temp)
    assert np.isclose(result, expected, atol=0.01), f"Expected {expected}, got {result}"


@pytest.mark.parametrize(
    "temp, dew_temp",
    [
        (-10.0, 263.15),  # Invalid: temperature in Kelvin cannot be negative
        (273.15, -5.0),  # Invalid: dew temperature in Kelvin cannot be negative
        (200.0, 300.0),  # Invalid: dew point cannot exceed air temperature
    ],
)
def test_calculate_relative_humidity_invalid_inputs(temp, dew_temp):
    with pytest.raises(ValueError):
        calculate_relative_humidity(temp, dew_temp)


@pytest.mark.skip(reason="herbie bug")
def test_select_station_data_values(monkeypatch, mock_herbie_find_grib):
    """Value verified with gdallocationinfo cli - gdallocationinfo subset_d5ef1aeb__20250114000000-0h-oper-fc.grib2 -wgs84 -126.928233 50.132417"""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    date = datetime(2025, 1, 14)
    cwd = os.path.dirname(__file__)
    H = Herbie(date, model="ifs", product="oper", save_dir=cwd)
    grib = H.download(TEMP)

    dataset = gdal.Open(grib)
    wkt = dataset.GetProjection()
    crs = CRS.from_string(wkt)
    geo_to_raster_transformer = get_transformer(NAD83_CRS, crs)

    processsor = process_grib_herbie.HerbieGribProcessor(cwd, geo_to_raster_transformer)
    stations_df = processsor.get_stations_dataframe()
    station_data = processsor.select_station_data(H, stations_df, [TEMP])

    station_code = stations_df.iloc[0].code
    herbie_value = station_data.sel(point_code=station_code)[TEMP_FIELD].item()

    gdallocationinfo_value = 1.47487792968752  # gdal converts values to celsius somehow
    herbie_value_celsius = herbie_value - 273.15  # ecmwf contains values in Kelvin

    assert herbie_value_celsius == pytest.approx(gdallocationinfo_value, 0.01)
