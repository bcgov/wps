""" Test machine learning code - collecting data, learning from data, and predicting a bias adjusted
result.
"""
from datetime import datetime
from typing import List
import pytest
from pytest_bdd import scenario, given, then, when
from app.db.models import PredictionModel, PredictionModelGridSubset
from app.models import machine_learning
from app.tests.models.crud import get_actuals_left_outer_join_with_predictions


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_left_outer_join_with_predictions',
                        get_actuals_left_outer_join_with_predictions)


@scenario("test_machine_learning.feature", "Learn weather",
          example_converters=dict(coordinate=eval,
                                  points=eval,
                                  model_temp=float,
                                  model_rh=float,
                                  timestamp=datetime.fromisoformat,
                                  bias_adjusted_temp=lambda value: None if value == 'None' else float(
                                      value),
                                  bias_adjusted_rh=lambda value: None if value == 'None' else float(value)))
def test_machine_learning():
    """ BDD Scenario for predictions """


@ given("An instance of StationMachineLearning for <coordinate> within <points>")
def given_an_instance(coordinate: List, points: List):
    """ Bind the data variable """
    return machine_learning.StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        grid=PredictionModelGridSubset(id=1),
        points=points,
        target_coordinate=coordinate,
        station_code=None,
        max_learn_date=datetime.now())
# pylint: disable=redefined-outer-name, unused-argument


@ when('The machine learns')
def learn(given_an_instance: machine_learning.StationMachineLearning,
          mock_get_actuals_left_outer_join_with_predictions: List):
    """ Train the machine learning model """
    given_an_instance.learn()
# pylint: enable=redefined-outer-name


# pylint: disable=redefined-outer-name
@ then('The <model_temp> for <timestamp> results in <bias_adjusted_temp>')
def assert_temperature(
        given_an_instance: machine_learning.StationMachineLearning,
        model_temp: float, timestamp: datetime, bias_adjusted_temp: float):
    """ Assert that the ML algorithm predicts the temperature correctly """
    result = given_an_instance.predict_temperature(model_temp, timestamp)
    assert result == bias_adjusted_temp
# pylint: enable=redefined-outer-name


# pylint: disable=redefined-outer-name
@ then('The <model_rh> for <timestamp> results in <bias_adjusted_rh>')
def assert_rh(given_an_instance: machine_learning.StationMachineLearning,
              model_rh: float, timestamp: datetime, bias_adjusted_rh: float):
    """ Assert that the ML algorithm predicts the relative humidity correctly """
    result = given_an_instance.predict_rh(model_rh, timestamp)
    assert result == bias_adjusted_rh
# pylint: enable=redefined-outer-name
