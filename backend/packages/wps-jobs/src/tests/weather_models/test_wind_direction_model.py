import math
import pytest
from datetime import datetime
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction
from weather_model_jobs.bias_adjusted_variable import WIND_DIRECTION
from weather_model_jobs.machine_learning import HourOfDayRegression
from weather_model_jobs.utils.wind_direction_utils import compute_u_v


# with this code's u, v convention: 10 km/h from 180° is [10, 0], 15 km/h from 90° is [0, -15]
PREDICTED_U_V = [10.0, 0.0]
OBSERVED_U_V = [0.0, -15.0]


@pytest.mark.parametrize(
    "actual, prediction, expected_x, expected_y",
    [
        # Happy path
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=15, wind_direction=90),
            ModelRunPrediction(wind_tgl_10=10, wdir_tgl_10=180),
            PREDICTED_U_V,
            OBSERVED_U_V,
        ),
        # No actual data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(wind_tgl_10=10, wdir_tgl_10=180),
            PREDICTED_U_V,
            None,
        ),
        # No prediction data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=15, wind_direction=90),
            ModelRunPrediction(),
            None,
            OBSERVED_U_V,
        ),
        # No actual or prediction data
        (HourlyActual(weather_date=datetime(2020, 10, 10, 18)), ModelRunPrediction(), None, None),
        # Only windspeed for actual
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=15),
            ModelRunPrediction(wind_tgl_10=10, wdir_tgl_10=180),
            PREDICTED_U_V,
            None,
        ),
        # Only wind direction for actual
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_direction=90),
            ModelRunPrediction(wind_tgl_10=10, wdir_tgl_10=180),
            PREDICTED_U_V,
            None,
        ),
        # Only windspeed for prediction
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=15, wind_direction=90),
            ModelRunPrediction(wind_tgl_10=10),
            None,
            OBSERVED_U_V,
        ),
        # Only wind direction for prediction
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=15, wind_direction=90),
            ModelRunPrediction(wdir_tgl_10=180),
            None,
            OBSERVED_U_V,
        ),
        # NaN actual wind speed
        (
            HourlyActual(
                weather_date=datetime(2020, 10, 10, 18), wind_speed=math.nan, wind_direction=90
            ),
            ModelRunPrediction(wind_tgl_10=10, wdir_tgl_10=180),
            PREDICTED_U_V,
            None,
        ),
    ],
)
def test_wind_direction_model_sample_values(actual, prediction, expected_x, expected_y):
    variable = WIND_DIRECTION

    x, y = variable.predicted(prediction), variable.observed(actual)

    assert x == (None if expected_x is None else pytest.approx(expected_x, abs=1e-9))
    assert y == (None if expected_y is None else pytest.approx(expected_y, abs=1e-9))


def test_wind_direction_regression_learns_u_v_relationship():
    regression = HourOfDayRegression()
    # observed wind is always the model wind, so the regression is the identity on u, v
    for speed, direction in ((10, 90), (15, 180), (5, 270), (20, 45)):
        u_v = compute_u_v(speed, direction)
        regression.add(18, u_v, u_v)

    regression.fit()

    expected = compute_u_v(12, 120)
    assert list(regression.predict(18, expected)) == pytest.approx(expected)


def test_wind_direction_regression_untrained_hour_returns_none():
    regression = HourOfDayRegression()
    regression.add(18, compute_u_v(10, 90), compute_u_v(10, 90))
    regression.fit()

    assert regression.predict(0, compute_u_v(10, 90)) is None
