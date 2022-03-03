from typing import Tuple
from distutils.util import strtobool
import pytest
from pytest_bdd import scenario, given
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockFixture
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file, load_json_file_with_name
from app.tests.hfi import mock_station_crud


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - request',
          example_converters=dict(request_json=load_json_file_with_name(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__),
                                  request_saved=strtobool))
def test_fire_behaviour_calculator_scenario_no_request_stored():
    """ BDD Scenario. """
    pass


@given("I received a <request_json>", target_fixture='result')
def given_request_none_stored(monkeypatch: pytest.MonkeyPatch, mocker: MockFixture, request_json: Tuple[dict, str]):
    """ Handle request
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # mock out database calls:
    mock_station_crud(monkeypatch)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return {
        'response': client.post('/api/hfi-calc/', headers=headers, json=request_json[0]),
        'filename': request_json[1]
    }
