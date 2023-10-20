

import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models.linear_model import LinearModel
from app.weather_models.wind_direction_model import WindDirectionModel


@pytest.mark.parametrize(
    "actual, prediction, call_count",
    [
        # Happy path
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18),
                         wind_speed=15,
                         wind_direction=90),
            ModelRunPrediction(wind_tgl_10=10,
                               wdir_tgl_10=97),
            1
        ),
        # No actual data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(wind_tgl_10=10,
                               wdir_tgl_10=97),
            0
        ),
        # No prediction data
        (
            HourlyActual(
                weather_date=datetime(2020, 10, 10, 18),
                wind_speed=15,
                wind_direction=90),
            ModelRunPrediction(),
            0
        ),
        # No actual or prediction data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(),
            0
        ),
        # Only windspeed for actual
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=10),
            ModelRunPrediction(wind_tgl_10=10,
                               wdir_tgl_10=97),
            0
        ),
        # Only wind direction for actual
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_direction=10),
            ModelRunPrediction(wind_tgl_10=10,
                               wdir_tgl_10=97),
            0
        ),
        # Only windspeed for prediction
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=10, wind_direction=90),
            ModelRunPrediction(wind_tgl_10=10),
            0
        ),

        # Only wind direction for prediction
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18), wind_speed=10, wind_direction=90),
            ModelRunPrediction(wdir_tgl_10=97),
            0
        ),
    ],
)
def test_wind_direction_model_sample_calls(mocker: MockerFixture, actual, prediction, call_count):
    mock_linear_model = LinearModel()
    append_x_y_mock = mocker.patch.object(mock_linear_model, "append_x_y")
    wind_dir_model = WindDirectionModel(linear_model=mock_linear_model)

    wind_dir_model.add_sample(prediction, actual)

    assert append_x_y_mock.call_count == call_count


def test_wind_direction_model_train(mocker: MockerFixture):
    mock_linear_model = LinearModel()
    append_x_y_mock = mocker.patch.object(mock_linear_model, "train")
    wind_dir_model = WindDirectionModel(linear_model=mock_linear_model)

    wind_dir_model.train()

    assert append_x_y_mock.call_count == 1


def test_wind_direction_model_predict(mocker: MockerFixture):
    mock_linear_model = LinearModel()
    append_x_y_mock = mocker.patch.object(mock_linear_model, "predict")
    wind_dir_model = WindDirectionModel(linear_model=mock_linear_model)

    wind_dir_model.predict(0, [[0, 0]])

    assert append_x_y_mock.call_count == 1
