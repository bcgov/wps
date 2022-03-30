from typing import Tuple
import pytest
from pytest_bdd import scenario, given, parsers
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import app.main
from app.db.models.hfi_calc import PlanningWeatherStation, FuelType, FireCentre, PlanningArea
from app.tests.common import default_mock_client_get
from app.tests import load_json_file_with_name
from app.tests.hfi import mock_station_crud


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - request')
def test_fire_behaviour_calculator_scenario_no_request_stored():
    """ BDD Scenario. """
    pass


@given(parsers.parse("I received a hfi-calc {url} {request_json} with {verb}"),
       target_fixture='response',
       converters={'request_json': load_json_file_with_name(__file__), 'url': str})
def given_request_none_stored(
        monkeypatch: pytest.MonkeyPatch, url: str, request_json: Tuple[dict, str], verb: str):
    """ Handle request
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

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    if verb == 'get':
        response = client.get(url, headers=headers)
    else:
        response = client.post(url, headers=headers, json=request_json[0])
    return {
        'response': response,
        'filename': request_json[1]
    }


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint_request.feature', 'HFI - pdf download')
def test_fire_behaviour_calculator_scenario_pdf_download():
    """ BDD Scenario. """
    pass
