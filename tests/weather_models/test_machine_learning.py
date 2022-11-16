""" Test machine learning code - collecting data, learning from data, and predicting a bias adjusted
result.
"""
from datetime import datetime
import pytest
from pytest_bdd import scenario, given, parsers, then, when
from tests import _load_json_file
from db.models import PredictionModel, PredictionModelGridSubset
from app.weather_models import machine_learning
from tests.weather_models.crud import get_actuals_left_outer_join_with_predictions
from tests.common import str2float


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_left_outer_join_with_predictions',
                        get_actuals_left_outer_join_with_predictions)


@pytest.mark.usefixtures('mock_get_actuals_left_outer_join_with_predictions')
@scenario("test_machine_learning.feature", "Learn weather")
def test_machine_learning():
    """ BDD Scenario for predictions """


@given(parsers.parse("An instance of StationMachineLearning"),
       target_fixture='instance')
def given_an_instance() -> machine_learning.StationMachineLearning:
    """ Bind the data variable """
    # super weird bug? with pytest_bdd that hooked into isoformat on the coordinate and points fields.
    # tried forever to figure out why - and gave up in the end. removed coordinate and point from
    # feature file and just loading it in here.
    coordinate = _load_json_file(__file__, 'coordinate.json')
    points = _load_json_file(__file__, 'points.json')
    return machine_learning.StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        grid=PredictionModelGridSubset(id=1),
        points=points,
        target_coordinate=coordinate,
        station_code=None,
        max_learn_date=datetime.now())


@when('The machine learns')
def learn(instance: machine_learning.StationMachineLearning):
    """ Train the machine learning model """
    instance.learn()


@then(parsers.parse('The model_temp: {model_temp} for {timestamp} results in {bias_adjusted_temp}'),
      converters=dict(
          model_temp=float,
          timestamp=datetime.fromisoformat,
          bias_adjusted_temp=str2float))
def assert_temperature(
        instance: machine_learning.StationMachineLearning,
        model_temp: float, timestamp: datetime, bias_adjusted_temp: float):
    """ Assert that the ML algorithm predicts the temperature correctly """
    result = instance.predict_temperature(model_temp, timestamp)
    assert result == bias_adjusted_temp


@then(parsers.parse('The model_rh: {model_rh} for {timestamp} results in {bias_adjusted_rh}'),
      converters=dict(
          model_rh=float,
          timestamp=datetime.fromisoformat,
          bias_adjusted_rh=str2float))
def assert_rh(instance: machine_learning.StationMachineLearning,
              model_rh: float, timestamp: datetime, bias_adjusted_rh: float):
    """ Assert that the ML algorithm predicts the relative humidity correctly """
    result = instance.predict_rh(model_rh, timestamp)
    assert result == bias_adjusted_rh
