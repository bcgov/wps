import pytest
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from wps_shared.db.models.weather_models import ModelRunPrediction
from weather_model_jobs.ecmwf_model_processor import ECMWFModelProcessor
from weather_model_jobs import ModelEnum, ModelRunInfo, ModelRunProcessResult, ProjectionEnum

TEST_DATETIME = datetime(2024, 10, 10, 6, tzinfo=timezone.utc)
MOCK_GRIB_URL = "mock_grib_url"


@pytest.fixture
def mock_herbie():
    mock = MagicMock()
    # Create a mock dataset for each weather parameter
    temp_ds = xr.Dataset.from_dict(
        {
            "coords": {
                "latitude": {"dims": ["latitude"], "data": [50.0, 49.75]},
                "longitude": {"dims": ["longitude"], "data": [10.0, 10.25]},
            },
            "data_vars": {
                "t2m": {
                    "dims": ["latitude", "longitude"],
                    "data": [[273.15, 273.16], [273.17, 273.18]],
                    "attrs": {"units": "K", "long_name": "air temperature"},
                }
            },
            "attrs": {
                "description": "Temperature dataset with consistent latitude, longitude, x, and y coordinates"
            },
        }
    )
    dew_temp_ds = xr.Dataset.from_dict(
        {
            "coords": {
                "latitude": {"dims": ["latitude"], "data": [50.0, 49.75]},
                "longitude": {"dims": ["longitude"], "data": [10.0, 10.25]},
            },
            "data_vars": {
                "d2m": {
                    "dims": ["latitude", "longitude"],
                    "data": [[273.15, 273.16], [273.17, 273.18]],
                    "attrs": {"units": "K", "long_name": "air temperature"},
                }
            },
            "attrs": {"description": "Trimmed dataset for testing purposes"},
        }
    )
    wind_ds = xr.Dataset.from_dict(
        {
            "coords": {
                "latitude": {"dims": ["latitude"], "data": [50.0, 49.75]},
                "longitude": {"dims": ["longitude"], "data": [10.0, 10.25]},
            },
            "data_vars": {
                "u10": {
                    "dims": ["latitude", "longitude"],
                    "data": [[5.0, 5.1], [4.9, 5.0]],
                    "attrs": {"units": "m/s", "long_name": "u-component of wind"},
                },
                "v10": {
                    "dims": ["latitude", "longitude"],
                    "data": [[3.0, 3.1], [2.9, 3.0]],
                    "attrs": {"units": "m/s", "long_name": "v-component of wind"},
                },
                "si10": {
                    "dims": ["latitude", "longitude"],
                    "data": [[5.83, 5.9], [5.7, 5.8]],
                    "attrs": {"units": "m/s", "long_name": "wind speed"},
                },
                "wdir10": {
                    "dims": ["latitude", "longitude"],
                    "data": [[30.96, 31.0], [30.5, 30.7]],
                    "attrs": {"units": "degrees", "long_name": "wind direction"},
                },
            },
            "attrs": {
                "description": "Wind dataset with consistent latitude, longitude, x, and y coordinates"
            },
        }
    )
    precip_ds = xr.Dataset.from_dict(
        {
            "coords": {
                "latitude": {"dims": ["latitude"], "data": [50.0, 49.75]},
                "longitude": {"dims": ["longitude"], "data": [10.0, 10.25]},
            },
            "data_vars": {
                "tp": {
                    "dims": ["latitude", "longitude"],
                    "data": [[0.2, 0.23], [0.2, 0.23]],
                    "attrs": {"units": "K", "long_name": "air temperature"},
                }
            },
            "attrs": {"description": "Trimmed dataset for testing purposes"},
        }
    )

    # Configure the mock to return these datasets
    def mock_xarray(param, *args, **kwargs):
        if param == ":2t:":
            return temp_ds
        elif param == ":2d:":
            return dew_temp_ds
        elif param == ":10[u|v]:":
            return wind_ds
        elif param == ":tp:":
            return precip_ds

    mock.xarray.side_effect = mock_xarray
    mock.grib = MOCK_GRIB_URL
    return mock


@pytest.fixture
def mock_stations_df():
    return pd.DataFrame({"point_code": [1], "latitude": [50.0], "longitude": [10.0]})


@pytest.fixture
def mock_model_run_info():
    return ModelRunInfo(
        model_enum=ModelEnum.ECMWF,
        model_run_timestamp=TEST_DATETIME,
        prediction_timestamp=TEST_DATETIME + timedelta(hours=0),
        projection=ProjectionEnum.ECMWF_LATLON,
    )


def test_process_grib_data(mock_herbie, mock_stations_df, mock_model_run_info):
    processor = ECMWFModelProcessor(working_directory="/tmp")

    result = processor.process_grib_data(
        herbie_instance=mock_herbie, grib_info=mock_model_run_info, stations_df=mock_stations_df
    )

    assert isinstance(result, ModelRunProcessResult)
    assert result.model_run_info == mock_model_run_info
    assert result.url == MOCK_GRIB_URL
    assert ModelRunPrediction.tmp_tgl_2.name in result.data
    assert ModelRunPrediction.rh_tgl_2.name in result.data
    assert ModelRunPrediction.apcp_sfc_0.name in result.data
    assert ModelRunPrediction.wind_tgl_10.name in result.data
    assert ModelRunPrediction.wdir_tgl_10.name in result.data
    assert result.data[ModelRunPrediction.tmp_tgl_2.name].values[0] == pytest.approx(
        0.0, rel=1e-6
    )  # kelvin to celsius
    assert result.data[ModelRunPrediction.rh_tgl_2.name].values[0] == pytest.approx(
        100.0, rel=1e-6
    )  # computed relative humidity
    assert result.data[ModelRunPrediction.apcp_sfc_0.name].values[0] == pytest.approx(
        200.0, rel=1e-6
    )  # m to mm
    assert result.data[ModelRunPrediction.wind_tgl_10.name].values[0] == pytest.approx(
        21.0, rel=1e-2
    )  # u, v to wind speed
    assert result.data[ModelRunPrediction.wdir_tgl_10.name].values[0] == pytest.approx(
        239.0, rel=1e-2
    )  # u, v to wind direction
