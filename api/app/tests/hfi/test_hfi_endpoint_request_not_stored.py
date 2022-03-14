
from typing import Tuple
from distutils.util import strtobool
import pytest
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockFixture
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file_with_name
from app.tests.hfi import mock_station_crud


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request_not_stored.feature', 'HFI - load request, no request stored')
def test_fire_behaviour_calculator_scenario_no_request_stored():
    """ BDD Scenario. """
    pass


@given(parsers.parse("I received a {request_json}, but don't have one stored"),
       target_fixture='response',
       converters=dict(request_json=load_json_file_with_name(__file__)))
def given_request_none_stored(monkeypatch: pytest.MonkeyPatch, mocker: MockFixture, request_json: Tuple[dict, str]):
    """ Handle request
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # mock out database calls:
    mock_station_crud(monkeypatch)

    store_spy = mocker.spy(app.routers.hfi_calc, 'store_hfi_request')

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return {
        'response': client.post('/api/hfi-calc/', headers=headers, json=request_json[0]),
        'filename': request_json[1],
        'saved': store_spy.call_count == 1
    }


@then(parsers.parse("request == saved = {request_saved}"), converters={'request_saved': strtobool})
def then_request_saved(response, request_saved: bool):
    """ Check request saved """
    assert response['saved'] == request_saved
