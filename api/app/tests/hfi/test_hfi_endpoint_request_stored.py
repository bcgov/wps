from typing import Tuple, List
import pytest
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockFixture
from app.db.models.hfi_calc import HFIRequest
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file, load_json_file_with_name
from app.tests.hfi import mock_station_crud, mock_planning_area_crud


def str_to_bool(input: str):
    return input == 'True'


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request_stored.feature', 'HFI - load request, request stored',
          example_converters=dict(request_json=load_json_file_with_name(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__),
                                  stored_request_json=load_json_file(__file__)))
def test_fire_behaviour_calculator_scenario_request_stored():
    """ BDD Scenario. """
    pass


@given("I received a <request_json>, and have one stored <stored_request_json>", target_fixture='result')
def given_request_have_one_stored(monkeypatch,
                                  request_json: Tuple[dict, str],
                                  stored_request_json: Tuple[dict, str]):
    """ Handle request
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # mock out database calls:
    mock_station_crud(monkeypatch)

    def mock_get_most_recent_updated_hfi_request(_, __):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        return HFIRequest(request=stored_request_json)

    monkeypatch.setattr(app.routers.hfi_calc, 'get_most_recent_updated_hfi_request',
                        mock_get_most_recent_updated_hfi_request)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return {
        'response': client.post('/api/hfi-calc/', headers=headers, json=request_json[0]),
        'filename': request_json[1]
    }
