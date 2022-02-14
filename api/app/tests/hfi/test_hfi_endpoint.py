
from typing import Tuple, List
import json
import pytest
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockFixture
from app.db.models.hfi_calc import HFIRequest, PlanningWeatherStation, PlanningArea
import app.main
from app.schemas.shared import FuelType
from app.tests.common import default_mock_client_get
from app.tests import load_json_file, load_json_file_with_name


def str_to_bool(input: str):
    return input == 'True'


def mock_planning_area_crud(monkeypatch):

    def mock_get_planning_areas(session, fire_centre_id):
        """ Returns mocked PlanningAreas. """
        return [PlanningArea(id=1, fire_centre_id=1, name='Area 1', order_of_appearance_in_list=1),
                PlanningArea(id=2, fire_centre_id=1, name='Area 2', order_of_appearance_in_list=2)]

    def mock_get_fire_centre_planning_area_stations(session, fire_centre_id):
        """ Returns mocked stations per PlanningAreas """
        return [PlanningWeatherStation(id=1, planning_area_id=1, station_code=230),
                PlanningWeatherStation(id=2, planning_area_id=2, station_code=239)]

    monkeypatch.setattr(app.hfi.hfi, 'get_planning_areas', mock_get_planning_areas)
    monkeypatch.setattr(app.hfi.hfi, 'get_fire_centre_planning_area_stations',
                        mock_get_fire_centre_planning_area_stations)


def mock_station_crud(monkeypatch):
    code1 = 230
    code2 = 239
    all_station_codes = [{'station_code': code1}, {'station_code': code2}]

    def mock_get_all_stations(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    def mock_get_station_with_fuel_types(_, station_codes: List[int]):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        result = []
        for station_code in station_codes:
            planning_station = PlanningWeatherStation(station_code=station_code)
            fuel_type = FuelType(abbrev='C3', description='C3')
            result.append((planning_station, fuel_type))
        return result

    monkeypatch.setattr(app.utils.hfi_calculator, 'get_all_stations', mock_get_all_stations)
    monkeypatch.setattr(app.wildfire_one.wfwx_api, 'get_stations_with_fuel_types',
                        mock_get_station_with_fuel_types)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint.feature', 'HFI - load request, no request stored',
          example_converters=dict(request_json=load_json_file_with_name(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__),
                                  request_saved=str_to_bool))
def test_fire_behaviour_calculator_scenario_no_request_stored():
    """ BDD Scenario. """
    pass


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_hfi_endpoint.feature', 'HFI - load request, request stored',
          example_converters=dict(request_json=load_json_file_with_name(__file__),
                                  status_code=int,
                                  response_json=load_json_file(__file__),
                                  stored_request_json=load_json_file(__file__)))
def test_fire_behaviour_calculator_scenario_request_stored():
    """ BDD Scenario. """
    pass


@given("I received a <request_json>, but don't have one stored", target_fixture='result')
def given_request_none_stored(monkeypatch: pytest.MonkeyPatch, mocker: MockFixture, request_json: Tuple[dict, str]):
    """ Handle request
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # mock out database calls:
    mock_station_crud(monkeypatch)
    mock_planning_area_crud(monkeypatch)

    store_spy = mocker.spy(app.routers.hfi_calc, 'store_hfi_request')

    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return {
        'response': client.post('/api/hfi-calc/', headers=headers, json=request_json[0]),
        'filename': request_json[1],
        'saved': store_spy.call_count == 1
    }


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


@then("request == saved = <request_saved>")
def then_request_saved(result, request_saved: bool):
    """ Check request saved """
    assert result['saved'] == request_saved
