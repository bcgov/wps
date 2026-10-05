import pytest
from datetime import datetime
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction
from weather_model_jobs.bias_adjusted_variable import TEMPERATURE
from weather_model_jobs.machine_learning import HourOfDayRegression


@pytest.mark.parametrize(
    "actual, prediction, expected_x, expected_y",
    [
        # Happy path
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), temperature=15),
            ModelRunPrediction(tmp_tgl_2=10),
            [10.0],
            [15.0],
        ),
        # No actual data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(tmp_tgl_2=10),
            [10.0],
            None,
        ),
        # No prediction data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), temperature=15),
            ModelRunPrediction(),
            None,
            [15.0],
        ),
        # No actual or prediction data
        (HourlyActual(weather_date=datetime(2020, 10, 10, 18)), ModelRunPrediction(), None, None),
    ],
)
def test_regression_model_sample_values(actual, prediction, expected_x, expected_y):
    variable = TEMPERATURE

    assert variable.predicted(prediction) == expected_x
    assert variable.observed(actual) == expected_y


def test_hour_of_day_regression_learns_linear_relationship():
    regression = HourOfDayRegression()
    # y = 2x + 1 at hour 18
    for x in (1.0, 2.0, 3.0):
        regression.add(18, [x], [2 * x + 1])

    regression.fit()

    assert regression.predict(18, [4.0])[0] == pytest.approx(9.0)


def test_hour_of_day_regression_untrained_hour_returns_none():
    regression = HourOfDayRegression()
    regression.add(18, [1.0], [1.0])
    regression.fit()

    # hours without samples have no model
    assert regression.predict(19, [1.0]) is None
