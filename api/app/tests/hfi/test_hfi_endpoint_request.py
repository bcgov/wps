from typing import Tuple
from distutils.util import strtobool
from unittest.mock import MagicMock
import pytest
import json
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockerFixture
import app.main
import app.routers.hfi_calc
from app.db.models.hfi_calc import PlanningWeatherStation, FuelType, FireCentre, PlanningArea, HFIRequest
from app.tests.common import default_mock_client_get
from app.tests import load_json_file
from app.tests.hfi import mock_station_crud


def _setup_mock(monkeypatch: pytest.MonkeyPatch):
    """ Prepare all our mocked out calls.
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    def mock_get_fire_weather_stations(_):
        fire_centre = FireCentre(id=1, name='Kamloops Fire Centre')
        planning_area_1 = PlanningArea(id=1, name='Kamloops (K2)', fire_centre_id=1,
                                       order_of_appearance_in_list=1)
        planning_area_2 = PlanningArea(id=2, name='Vernon (K4)', fire_centre_id=1,
                                       order_of_appearance_in_list=2)
        fuel_type_1 = FuelType(abbrev='O1B', description='neigh', fuel_type_code="O1B",
                               percentage_conifer=0, percentage_dead_fir=0)
        fuel_type_2 = FuelType(abbrev='C7B', description='moo', fuel_type_code='C7',
                               percentage_conifer=100, percentage_dead_fir=0)
        return (
            (PlanningWeatherStation(station_code=230, fuel_type_id=1,
             planning_area_id=1), fuel_type_1, planning_area_1, fire_centre),
            (PlanningWeatherStation(station_code=239, fuel_type_id=2,
             planning_area_id=2), fuel_type_2, planning_area_2, fire_centre)
        )

    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_weather_stations', mock_get_fire_weather_stations)

    # mock out database calls:
    mock_station_crud(monkeypatch)


def _setup_mock_with_role(monkeypatch: pytest.MonkeyPatch, role: str):
    """ Prepare jwt decode to be mocked with permission
    """
    _setup_mock(monkeypatch)

    class MockJWTDecodeSetFireStarts:
        """ Mock pyjwt module with set fire starts permissions """

        def __init__(self):
            self.decoded_token = {
                "preferred_username": "test_username",
                "resource_access": {
                    "wps-web": {
                        "roles": [
                            "hfi_set_fire_starts"
                        ]
                    }
                }}

        def __getitem__(self, key):
            return self.decoded_token[key]

        def get(self, key, _):
            "Returns the mock decoded token"
            return self.decoded_token[key]

        def decode(self):
            "Returns the mock decoded token"
            return self.decoded_token

    def mock_fire_start_permission_function(*args, **kwargs):  # pylint: disable=unused-argument
        return MockJWTDecodeSetFireStarts()

    if(role == 'hfi_set_fire_starts'):
        monkeypatch.setattr("jwt.decode", mock_fire_start_permission_function)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - GET request')
def test_fire_behaviour_calculator_get_scenario():
    """ BDD Scenario. """
    pass


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - POST request')
def test_fire_behaviour_calculator_post_scenario():
    """ BDD Scenario. """
    pass


@given('I spy on store_hfi_request', target_fixture='spy_store_hfi_request')
def spy_on_store_hfi_request(mocker: MockerFixture):
    return mocker.spy(app.routers.hfi_calc, 'store_hfi_request')


@given(parsers.parse("I have a stored request {stored_request_json}"),
       converters={'stored_request_json': load_json_file(__file__)})
def given_stored_request(monkeypatch, stored_request_json: Tuple[dict, str]):
    def mock_get_most_recent_updated_hfi_request(*_, **__):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        return HFIRequest(request=json.dumps(stored_request_json))

    monkeypatch.setattr(app.routers.hfi_calc, 'get_most_recent_updated_hfi_request',
                        mock_get_most_recent_updated_hfi_request)


@given(parsers.parse("I received a GET request for hfi-calc {url}"),
       target_fixture='response',
       converters={'url': str})
def given_hfi_calc_url_get(monkeypatch: pytest.MonkeyPatch, url: str):
    """ Handle request
    """
    _setup_mock(monkeypatch)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    response = client.get(url, headers=headers)
    return {
        'response': response
    }


@given(parsers.parse("I received a POST request for hfi-calc {url} with {role}"),
       target_fixture='response',
       converters={'url': str, 'role': str})
def given_hfi_calc_url_post(monkeypatch: pytest.MonkeyPatch, url: str, role: str):
    """ Handle request
    """
    _setup_mock_with_role(monkeypatch, role)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    response = client.post(url, headers=headers)
    return {
        'response': response
    }


@then(parsers.parse("request == saved = {request_saved}"), converters={'request_saved': strtobool})
def then_request_saved(spy_store_hfi_request: MagicMock, request_saved: bool):
    assert spy_store_hfi_request.called == request_saved


@then("the response isn't cached")
def then_response_not_cached(response):
    """ Check that the response isn't being cached """

    # Unauthorized responses do not have cache-control set
    if 'cache-control' in response['response'].headers:
        assert response['response'].headers['cache-control'] == 'max-age=0'
