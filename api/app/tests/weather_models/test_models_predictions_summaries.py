""" Functional testing for /models/{model}/predictions/ endpoint.
"""
import os
import json
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import app.main
from app.tests import load_sqlalchemy_response_from_json


@ scenario("test_models_predictions_summaries.feature", "Get model prediction summaries from database")
def test_model_predictions_summaries_scenario():
    """ BDD Scenario for prediction summaries """


@ given("A database <sql_response>")
def given_a_database(monkeypatch, sql_response: str):
    """ Mock the sql response """

    def mock_get_data(*args):  # pylint: unused-argument
        return load_sqlalchemy_response_from_json(sql_response)

    monkeypatch.setattr(app.weather_models.fetch.summaries,
                        'get_station_model_predictions_order_by_prediction_timestamp', mock_get_data)
    return {}


@ given("station <codes>")
def given_stations(codes):
    """ evaluate string and return array of station codes. """
    return eval(codes)  # pylint: disable=eval-used


# pylint: disable=redefined-outer-name, unused-argument
@ when("I call <endpoint>")
def when_prediction(mock_jwt_decode, given_a_database, given_stations, endpoint: str):
    """ Make call to endpoint """
    client = TestClient(app.main.app)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': given_stations})
    given_a_database['response_json'] = response.json()
# pylint: enable=redefined-outer-name, unused-argument


# pylint: disable=redefined-outer-name, unused-argument
@then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert given_a_database['response_json'] == expected_json
# pylint: enable=redefined-outer-name, unused-argument
