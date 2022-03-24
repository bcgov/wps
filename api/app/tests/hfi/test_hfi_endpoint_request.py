from typing import Tuple
import pytest
from pytest_bdd import scenario, given, parsers
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file_with_name
from app.db.models.hfi_calc import PlanningWeatherStation, FuelType
from app.tests.hfi import mock_station_crud


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - request')
def test_fire_behaviour_calculator_scenario_no_request_stored():
    """ BDD Scenario. """
    pass


@given(parsers.parse("I received a hfi-calc {url} {request_json}"),
       target_fixture='response',
       converters={'request_json': load_json_file_with_name(__file__), 'url': str})
def given_request_none_stored(monkeypatch: pytest.MonkeyPatch, url: str, request_json: Tuple[dict, str]):
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
        'response': client.post(url, headers=headers, json=request_json[0]),
        'filename': request_json[1]
    }
