import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models.linear_model import LinearModel
from app.weather_models.regression_model import RegressionModel
from app.weather_models.sample import Samples


@pytest.mark.parametrize(
    "actual, prediction, call_count",
    [
        # Happy path
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18),
                         temperature=15),
            ModelRunPrediction(tmp_tgl_2=10),
            1
        ),
        # No actual data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(tmp_tgl_2=10),
            0
        ),
        # No prediction data
        (
            HourlyActual(
                weather_date=datetime(2020, 10, 10, 18),
                temperature=15),
            ModelRunPrediction(),
            0
        ),
        # No actual or prediction data
        (
            HourlyActual(weather_date=datetime(2020, 10, 10, 18)),
            ModelRunPrediction(),
            0
        )
    ],
)
def test_regression_model_sample_calls(mocker: MockerFixture, actual, prediction, call_count):
    mock_linear_model = LinearModel(samples=Samples())
    append_x_y_mock = mocker.patch.object(mock_linear_model, "append_x_y")
    regression_model = RegressionModel(model_key=ModelRunPrediction.tmp_tgl_2.name, linear_model=mock_linear_model)

    regression_model.add_sample(prediction, actual)

    assert append_x_y_mock.call_count == call_count


def test_regression_model_train(mocker: MockerFixture):
    mock_linear_model = LinearModel(samples=Samples())
    append_x_y_mock = mocker.patch.object(mock_linear_model, "train")
    regression_model = RegressionModel(model_key='test', linear_model=mock_linear_model)

    regression_model.train()

    assert append_x_y_mock.call_count == 1


def test_regression_model_predict(mocker: MockerFixture):
    mock_linear_model = LinearModel(samples=Samples())
    append_x_y_mock = mocker.patch.object(mock_linear_model, "predict")
    regression_model = RegressionModel(model_key='test', linear_model=mock_linear_model)

    regression_model.predict(0, [[0, 0]])

    assert append_x_y_mock.call_count == 1
