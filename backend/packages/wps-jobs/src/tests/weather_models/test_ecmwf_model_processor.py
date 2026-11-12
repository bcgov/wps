from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from weather_model_jobs import ModelEnum, ModelRunInfo, ModelRunProcessResult, ProjectionEnum
from weather_model_jobs.ecmwf_model_processor import ECMWFModelProcessor, crop_to_bc
from wps_shared.db.models.weather_models import ModelRunPrediction

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
                "longitude": {"dims": ["longitude"], "data": [-120.0, -119.75]},
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
                "longitude": {"dims": ["longitude"], "data": [-120.0, -119.75]},
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
                "longitude": {"dims": ["longitude"], "data": [-120.0, -119.75]},
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
                "longitude": {"dims": ["longitude"], "data": [-120.0, -119.75]},
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
    return pd.DataFrame({"code": [1], "latitude": [50.0], "longitude": [-120.0]})


@pytest.fixture
def mock_model_run_info():
    return ModelRunInfo(
        model_enum=ModelEnum.ECMWF,
        model_run_timestamp=TEST_DATETIME,
        prediction_timestamp=TEST_DATETIME + timedelta(hours=0),
        projection=ProjectionEnum.ECMWF_LATLON_0_1,
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


@pytest.mark.parametrize("reverse_latitude", [False, True])
@pytest.mark.parametrize("positive_longitude", [False, True])
def test_crop_to_bc_retains_buffer_and_source_coordinates(reverse_latitude, positive_longitude):
    latitude = np.array([46.9, 47, 48, 60, 61, 61.1])
    longitude = np.array([-140.1, -140, -139, -114, -113, -112.9])
    if reverse_latitude:
        latitude = latitude[::-1]
    if positive_longitude:
        longitude = longitude % 360
    values = np.arange(36).reshape(6, 6)
    dataset = xr.Dataset(
        {"t2m": (("latitude", "longitude"), values)},
        coords={"latitude": latitude, "longitude": longitude},
    )

    cropped = crop_to_bc(dataset)

    np.testing.assert_array_equal(cropped.latitude, latitude[1:-1])
    np.testing.assert_array_equal(cropped.longitude, longitude[1:-1])
    np.testing.assert_array_equal(cropped.t2m, values[1:-1, 1:-1])
    assert not np.shares_memory(cropped.t2m.values, dataset.t2m.values)


@pytest.mark.parametrize("missing_dimension", ["latitude", "longitude"])
def test_crop_to_bc_rejects_empty_crop(missing_dimension):
    dataset = xr.Dataset(coords={"latitude": [50.0], "longitude": [-120.0]})
    dataset = dataset.assign_coords({missing_dimension: [0.0]})

    with pytest.raises(ValueError, match="no grid points within buffered BC bounds"):
        crop_to_bc(dataset)


@pytest.mark.parametrize(
    "latitude, longitude", [(46.9, -120), (61.1, -120), (50, -140.1), (50, -112.9)]
)
def test_process_grib_data_rejects_stations_outside_crop(
    mock_herbie, mock_model_run_info, latitude, longitude
):
    stations = pd.DataFrame({"code": [987], "latitude": [latitude], "longitude": [longitude]})

    with pytest.raises(ValueError, match=r"outside buffered BC bounds: \[987\]"):
        ECMWFModelProcessor("/tmp").process_grib_data(mock_herbie, mock_model_run_info, stations)

    mock_herbie.xarray.assert_not_called()


@pytest.mark.parametrize("reverse_latitude", [False, True])
@pytest.mark.parametrize("positive_longitude", [False, True])
def test_cropped_sampling_matches_full_grid(reverse_latitude, positive_longitude):
    latitude = np.array([46, 47, 48, 49, 50, 59, 60, 61, 62])
    longitude = np.array([-141, -140, -139, -138, -120, -115, -114, -113, -112])
    if reverse_latitude:
        latitude = latitude[::-1]
    if positive_longitude:
        longitude = longitude % 360
    values = np.arange(81).reshape(9, 9).astype(float)
    dataset = xr.Dataset(
        {
            "t2m": (("latitude", "longitude"), values + 273.15),
            "u10": (("latitude", "longitude"), values / 10),
            "v10": (("latitude", "longitude"), -values / 20),
        },
        coords={"latitude": latitude, "longitude": longitude},
    )
    stations = pd.DataFrame(
        {
            "code": [1, 2, 3, 4],
            "latitude": [48.03, 59.97, 47.1, 60.9],
            "longitude": [-138.97, -114.03, -139.9, -113.1],
        }
    )

    expected = (
        dataset.copy(deep=True)
        .herbie.with_wind()
        .herbie.pick_points(stations, method="nearest", use_cached_tree=False)
    )
    actual = (
        crop_to_bc(dataset)
        .herbie.pick_points(stations, method="nearest", use_cached_tree=False)
        .herbie.with_wind()
    )

    xr.testing.assert_allclose(actual, expected)
