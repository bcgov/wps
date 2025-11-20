import pytest
import numpy as np
from wps_shared.db.models.weather_models import ModelRunPrediction

@pytest.fixture
def mock_model_run_prediction_numbers():
    """Fixture to create a mock ModelRunPrediction instance."""
    mock_instance = ModelRunPrediction()
    mock_instance.id = 1
    mock_instance.tmp_tgl_2 = 25.0
    mock_instance.rh_tgl_2 = 60.0
    mock_instance.apcp_sfc_0 = 5.0
    mock_instance.wdir_tgl_10 = 180.0
    mock_instance.wind_tgl_10 = 10.0
    return mock_instance

@pytest.fixture
def mock_model_run_prediction_numpy(mock_model_run_prediction_numbers):
    """Fixture to create a mock ModelRunPrediction instance."""
    mock_instance = ModelRunPrediction()
    mock_instance.id = 1
    mock_instance.tmp_tgl_2 = np.float64(mock_model_run_prediction_numbers.tmp_tgl_2)
    mock_instance.rh_tgl_2 = np.float64(mock_model_run_prediction_numbers.rh_tgl_2)
    mock_instance.apcp_sfc_0 = np.float64(mock_model_run_prediction_numbers.apcp_sfc_0)
    mock_instance.wdir_tgl_10 = np.float64(mock_model_run_prediction_numbers.wdir_tgl_10)
    mock_instance.wind_tgl_10 = np.float64(mock_model_run_prediction_numbers.wind_tgl_10)
    return mock_instance

@pytest.fixture
def mock_model_run_prediction_none():
    """Fixture to create a mock ModelRunPrediction instance."""
    return ModelRunPrediction()

@pytest.mark.parametrize("method, expected", [
    ("get_temp", 25.0),
    ("get_rh", 60.0),
    ("get_precip", 5.0),
    ("get_wind_speed", 10.0),
    ("get_wind_direction", 180.0),
])
def test_model_run_prediction(mock_model_run_prediction_numbers, mock_model_run_prediction_numpy, method, expected):
    """Parametrized test for ModelRunPrediction methods."""
    number_result = getattr(mock_model_run_prediction_numbers, method)()
    numpy_result = getattr(mock_model_run_prediction_numpy, method)()
    assert number_result == expected
    assert numpy_result == expected

@pytest.mark.parametrize("method, expected", [
    ("get_temp", None),
    ("get_rh", None),
    ("get_precip", pytest.approx(0.0, rel=0.1)),
    ("get_wind_speed", None),
    ("get_wind_direction", None),
])
def test_model_run_prediction_none(mock_model_run_prediction_none, method, expected):
    """Parametrized test for ModelRunPrediction methods."""
    result = getattr(mock_model_run_prediction_none, method)()
    assert result == expected