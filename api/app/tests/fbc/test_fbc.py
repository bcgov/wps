"""
Unit tests for fire behavour calculator.
"""
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
import pytest
import app.main
from app.tests import load_json_file


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fbc.feature', 'Fire Behaviour Calculation',
          example_converters=dict(request_json=load_json_file(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__)))
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given("I received a <request_json>", target_fixture='response')
def given_request(request_json: dict):
    """ Handle request
    Our request should result in
    1) station list requests to WFWX, to map station codes to GUIDs.
    2) dailies call to WFWX.
    3) call to the R code to caclulate values.
    """
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/fire_behaviour_calculator', headers=headers, json=request_json)


@then("the response status code is <status_code>")
def then_status(response, status_code: int):
    """ Check response status code """
    assert response.status_code == status_code


@then("the response is <response_json>")
def then_response(response, response_json: dict):
    """ Check entire response """
    assert response.json() == response_json
