from pytest_mock import MockerFixture
from app.weather_models.linear_model import LinearModel
from app.weather_models.regression_model import RegressionModel
from app.weather_models.sample import Samples


def test_regression_model_predict(mocker: MockerFixture):
    mock_linear_model = LinearModel(samples=Samples())
    append_x_y_mock = mocker.patch.object(mock_linear_model, "predict")
    regression_model = RegressionModel(model_key='test', linear_model=mock_linear_model)

    regression_model.predict(0, [[0, 0]])

    assert append_x_y_mock.call_count == 1
