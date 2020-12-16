""" Functional testing for /models/* endpoints.
"""
import os
import json
import importlib
import logging
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import app.main
from app.tests import load_sqlalchemy_response_from_json


logger = logging.getLogger(__name__)


@ scenario("test_models_endpoints.feature", "Generic model endpoint testing")
def test_model_predictions_summaries_scenario():
    """ BDD Scenario for prediction summaries """


def _patch_function(monkeypatch, module_name, function_name, json_filename):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*args):  # pylint: disable=unused-argument
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, json_filename)
        return load_sqlalchemy_response_from_json(filename)

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


@given("some explanatory <notes>")
def given_some_notes(notes: str):
    """ Send notes to the logger. """
    logger.info(notes)


@ given("A <crud_mapping>")
def given_a_database(monkeypatch, crud_mapping: str):
    """ Mock the sql response """

    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, crud_mapping)
    with open(filename) as crud_mappings_file:
        for item in json.load(crud_mappings_file):
            _patch_function(monkeypatch, item['module'], item['function'], item['json'])

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
    if response.status_code == 200:
        given_a_database['response_json'] = response.json()
    given_a_database['status_code'] = response.status_code
# pylint: enable=redefined-outer-name, unused-argument


@ then('The <expected_status_code> is matched')
def assert_status_code(given_a_database, expected_status_code: str):  # pylint: disable=redefined-outer-name
    """ Assert that the status code is as expected
    """
    assert given_a_database['status_code'] == int(expected_status_code)

# pylint: disable=redefined-outer-name, unused-argument


@ then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as expected_json_file:
        expected_json = json.load(expected_json_file)
        assert given_a_database['response_json'] == expected_json
# pylint: enable=redefined-outer-name, unused-argument
