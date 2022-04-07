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
from app.tests import load_json_file_with_name, load_json_file
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


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - request')
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """
    pass


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - pdf download')
def test_fire_behaviour_calculator_pdf_scenario():
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


@given(parsers.parse("I received a hfi-calc {url} with {verb}"),
       target_fixture='response',
       converters={'url': str, 'verb': str})
def given_hfi_calc_url(monkeypatch: pytest.MonkeyPatch, url: str, verb: str):
    """ Handle request
    """
    _setup_mock(monkeypatch)

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    if verb == 'get':
        response = client.get(url, headers=headers)
    else:
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
    assert response['response'].headers['cache-control'] == 'max-age=0'
