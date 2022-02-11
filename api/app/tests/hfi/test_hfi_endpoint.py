
from typing import Tuple
import json
import pytest
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file, load_json_file_with_name


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint.feature', 'Head Fire Intensity Calculation',
          example_converters=dict(request_json=load_json_file_with_name(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__)))
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given("I received a <request_json>", target_fixture='result')
def given_request(monkeypatch, request_json: Tuple[dict, str]):
    """ Handle request
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return {
        'response': client.post('/api/hfi-calc/', headers=headers, json=request_json[0]),
        'filename': request_json[1]
    }


@then("the response status code is <status_code>")
def then_status(result, status_code: int):
    """ Check response status code """
    assert result['response'].status_code == status_code, result['filename']


@then("the response is <response_json>")
def then_response(result, response_json: dict):
    """ Check entire response """
    if response_json is not None:
        print('actual:\n{}'.format(json.dumps(result['response'].json(), indent=4)))
        print('expected:\n{}'.format(json.dumps(response_json, indent=4)))
        assert result['response'].json() == response_json, result['filename']
