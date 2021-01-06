""" Functional testing for /models/* endpoints.
"""
import os
import json
import importlib
import logging
import pytest
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import app.main
from app.tests import load_sqlalchemy_response_from_json
from app.tests import load_json_file


logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario("test_models_endpoints.feature", "Generic model endpoint testing",
          example_converters=dict(
              codes=json.loads, endpoint=str, crud_mapping=load_json_file(__file__), expected_status_code=int,
              expected_response=load_json_file(__file__), notes=str))
def test_model_predictions_summaries_scenario():
    """ BDD Scenario for prediction summaries """


def _patch_function(monkeypatch, module_name: str, function_name: str, json_filename: str):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*_):
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, json_filename)
        return load_sqlalchemy_response_from_json(filename)

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


@given("some explanatory <notes>")
def given_some_notes(notes: str):
    """ Send notes to the logger. """
    logger.info(notes)


@given("A <crud_mapping>", target_fixture='database')
def given_a_database(monkeypatch, crud_mapping: dict):
    """ Mock the sql response """

    for item in crud_mapping:
        _patch_function(monkeypatch, item['module'], item['function'], item['json'])

    return {}


@when("I call <endpoint> with <codes>")
def when_prediction(database: dict, codes: str, endpoint: str):
    """ Make call to endpoint """
    client = TestClient(app.main.app)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': codes})
    if response.status_code == 200:
        database['response_json'] = response.json()
    database['status_code'] = response.status_code


@then('The <expected_status_code> is matched')
def assert_status_code(database: dict, expected_status_code: str):
    """ Assert that the status code is as expected
    """
    assert database['status_code'] == int(expected_status_code)


@then('The <expected_response> is matched')
def assert_response(database: dict, expected_response: dict):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    assert database['response_json'] == expected_response
