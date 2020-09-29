""" Test machine learning code - collecting data, learning from data, and predicting a bias adjusted
result.
"""
from datetime import datetime
import pytest
from pytest_bdd import scenario, given, then, when
from app.db.models import PredictionModel, PredictionModelGridSubset
from app.models import machine_learning
from app.tests.models.crud import get_actuals_outer_join_with_predictions


@pytest.fixture()
def mock_get_actuals_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_outer_join_with_predictions',
                        get_actuals_outer_join_with_predictions)


@scenario("test_machine_learning.feature", "Learn weather")
def test_machine_learning():
    """ BDD Scenario for predictions """


@given("An instance of StationMachineLearning")
def given_an_instance(mock_session):  # pylint: disable=redefined-outer-name,unused-argument
    """ Bind the data variable """
    return machine_learning.StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        grid=PredictionModelGridSubset(id=1),
        points=None,
        target_coordinate=None,
        station_code=None,
        max_learn_date=datetime.now())

# pylint: disable=redefined-outer-name, unused-argument


@when('The machine learns')
def learn(given_an_instance, mock_get_actuals_outer_join_with_predictions):
    """ Train the machine learning model """
    given_an_instance.learn()
# pylint: enable=redefined-outer-name


@then('The <model_temp> for <timestamp> results in <bias_adjusted_temp>')
def test_temperature(given_an_instance,  # pylint: disable=redefined-outer-name
                     model_temp, timestamp, bias_adjusted_temp):
    """ Assert that the ML algorithm predicts the temperature correctly """
    timestamp = datetime.fromisoformat(timestamp)
    result = given_an_instance.predict_temperature(model_temp, timestamp)
    assert result == bias_adjusted_temp


@then('The <model_rh> for <timestamp> results in <bias_adjusted_rh>')
def test_rh(given_an_instance, model_rh, timestamp, bias_adjusted_rh):  # pylint: disable=redefined-outer-name
    """ Assert that the ML algorithm predicts the relative humidity correctly """
    timestamp = datetime.fromisoformat(timestamp)
    result = given_an_instance.predict_rh(model_rh, timestamp)
    assert result == bias_adjusted_rh
