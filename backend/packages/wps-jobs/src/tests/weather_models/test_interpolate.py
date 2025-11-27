import pytest
from weather_model_jobs.utils.interpolate import (
    construct_interpolated_noon_prediction,
    SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION,
    interpolate_between_two_points,
    interpolate_wind_direction,
)
from datetime import datetime
from wps_shared.db.models.weather_models import ModelRunPrediction
import math


prediction_a_timestamp = datetime(2024, 5, 1, 18, 0, 0)
prediction_b_timestamp = datetime(2024, 5, 1, 21, 0, 0)


def generate_model_run_prediction(
    prediction_datetime: datetime, weather_values: float
) -> ModelRunPrediction:
    model_prediction = ModelRunPrediction(
        prediction_timestamp=prediction_datetime,
        tmp_tgl_2=weather_values,
        rh_tgl_2=weather_values,
        apcp_sfc_0=weather_values,
        wind_tgl_10=weather_values,
        wdir_tgl_10=weather_values,
    )
    return model_prediction


def test_construct_interpolated_noon_prediction():
    prediction_a = generate_model_run_prediction(prediction_a_timestamp, 1.0)
    prediction_b = generate_model_run_prediction(prediction_b_timestamp, 4.0)
    linear_interp_val = 3.0

    noon_prediction = construct_interpolated_noon_prediction(
        prediction_a, prediction_b, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
    )
    assert noon_prediction.prediction_timestamp.hour == 20
    assert math.isclose(noon_prediction.apcp_sfc_0, linear_interp_val, abs_tol=0)
    assert math.isclose(noon_prediction.rh_tgl_2, linear_interp_val, abs_tol=0)
    assert math.isclose(noon_prediction.wdir_tgl_10, linear_interp_val, abs_tol=0)
    assert math.isclose(noon_prediction.wind_tgl_10, linear_interp_val, abs_tol=0)
    assert math.isclose(noon_prediction.tmp_tgl_2, linear_interp_val, abs_tol=0)


def test_construct_interpolated_noon_prediction_empty():
    prediction_a = generate_model_run_prediction(prediction_a_timestamp, None)
    prediction_b = generate_model_run_prediction(prediction_b_timestamp, None)

    noon_prediction = construct_interpolated_noon_prediction(
        prediction_a, prediction_b, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
    )
    assert noon_prediction.prediction_timestamp.hour == 20
    assert noon_prediction.apcp_sfc_0 is None
    assert noon_prediction.rh_tgl_2 is None
    assert noon_prediction.wdir_tgl_10 is None
    assert noon_prediction.wind_tgl_10 is None
    assert noon_prediction.tmp_tgl_2 is None


def test_interpolate_between_two_points():
    interp_value = interpolate_between_two_points(1, 4, 1, 4, 3)
    assert interp_value == 3


def test_interpolate_between_two_points_with_none():
    interp_value = interpolate_between_two_points(1, 4, None, 4, 3)
    assert interp_value is None


@pytest.mark.parametrize(
    "wdir_a,wdir_b",
    [
        # prediction_a has no wind direction
        (None, 1),
        # prediction_b has no wind direction
        (1, None),
        # both predictions have no wind direction
        (1, None),
    ],
)
def test_empty_wind_direction_interpolation(wdir_a, wdir_b):
    prediction_a = generate_model_run_prediction(datetime(2024, 5, 1, 18, 0, 0), wdir_a)
    prediction_b = generate_model_run_prediction(datetime(2024, 5, 1, 18, 0, 0), wdir_b)
    assert (
        interpolate_wind_direction(prediction_a, prediction_b, datetime(2024, 5, 1, 18, 0, 0))
        is None
    )
