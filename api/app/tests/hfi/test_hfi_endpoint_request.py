from typing import Tuple
from distutils.util import strtobool
from unittest.mock import MagicMock
import pytest
import json
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from aiohttp import ClientSession
from pytest_mock import MockerFixture
import app.main
import app.routers.hfi_calc
from app.tests.common import default_mock_client_get
from app.tests import load_json_file
from app.db.models.hfi_calc import (PlanningWeatherStation, FuelType, FireCentre, PlanningArea,
                                    HFIRequest, FireStartRange, FireStartLookup)


def _setup_mock(monkeypatch: pytest.MonkeyPatch):
    """ Prepare all our mocked out calls.
    """
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    fuel_type_1 = FuelType(id=1, abbrev='O1B', fuel_type_code='O1B', description='O1B',
                           percentage_conifer=0, percentage_dead_fir=0)
    fuel_type_2 = FuelType(id=2, abbrev='C7B', fuel_type_code='C7B', description='C7B',
                           percentage_conifer=100, percentage_dead_fir=0)
    fuel_type_3 = FuelType(id=3, abbrev='C3', fuel_type_code='C3', description='C3',
                           percentage_conifer=100, percentage_dead_fir=0)

    def mock_get_fire_weather_stations(_):
        fire_centre = FireCentre(id=1, name='Kamloops Fire Centre')
        planning_area_1 = PlanningArea(id=1, name='Kamloops (K2)', fire_centre_id=1,
                                       order_of_appearance_in_list=1)
        planning_area_2 = PlanningArea(id=2, name='Vernon (K4)', fire_centre_id=1,
                                       order_of_appearance_in_list=2)
        return (
            (PlanningWeatherStation(station_code=230, fuel_type_id=1,
                                    planning_area_id=1), fuel_type_1, planning_area_1, fire_centre),
            (PlanningWeatherStation(station_code=239, fuel_type_id=1,
                                    planning_area_id=1), fuel_type_1, planning_area_1, fire_centre),
            (PlanningWeatherStation(station_code=230, fuel_type_id=2,
                                    planning_area_id=2), fuel_type_2, planning_area_2, fire_centre)
        )

    code1 = 230
    code2 = 239
    all_station_codes = [{'station_code': code1}, {'station_code': code2}]

    def mock_get_all_stations(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    def mock_get_fire_centre_stations(_, __: int):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        def get_fuel_type_by_station_code(code: int):
            if code == code1:
                return fuel_type_3
            return fuel_type_2
        result = []
        for station_code, planning_area_id in [(code1, 1), (code2, 1), (code1, 2)]:
            planning_station = PlanningWeatherStation(
                station_code=station_code, planning_area_id=planning_area_id)
            fuel_type = get_fuel_type_by_station_code(station_code)
            result.append((planning_station, fuel_type))
        return result

    def mock_get_fire_centre_fire_start_ranges(_, __: int):
        """ Returns mocked FireStartRange """
        data = ((1, '0-1'), (2, '1-2'), (3, '2-3'), (4, '3-6'), (5, '6+'))
        return [FireStartRange(id=id, label=range) for id, range in data]

    def mock_get_fire_start_lookup(_):
        """ Returns mocked FireStartLookup """
        data = ((1, 1, 1, 1),
                (2, 1, 2, 1),
                (3, 1, 3, 2),
                (4, 1, 4, 3),
                (5, 1, 5, 4),
                (6, 2, 1, 1),
                (7, 2, 2, 1),
                (8, 2, 3, 2),
                (9, 2, 4, 4),
                (10, 2, 5, 5),
                (11, 3, 1, 2),
                (12, 3, 2, 3),
                (13, 3, 3, 4),
                (14, 3, 4, 5),
                (15, 3, 5, 6),
                (16, 4, 1, 3),
                (17, 4, 2, 4),
                (18, 4, 3, 4),
                (19, 4, 4, 5),
                (20, 4, 5, 6),
                (21, 5, 1, 4),
                (22, 5, 2, 5),
                (23, 5, 3, 6),
                (24, 5, 4, 6),
                (25, 5, 5, 6))
        return [FireStartLookup(id=id,
                                fire_start_range_id=fire_start_range_id,
                                mean_intensity_group=mean_intensity_group,
                                prep_level=prep_level) for
                id, fire_start_range_id, mean_intensity_group, prep_level in data]

    fuel_types = [
        fuel_type_1,
        fuel_type_2,
        fuel_type_3
    ]

    def mock_get_fuel_type_by_id(_, fuel_type_id: int):
        """ Returns mocked FuelType """
        try:
            return next(fuel_type for fuel_type in fuel_types if fuel_type.id == fuel_type_id)
        except StopIteration:
            return None

    def mock_get_fuel_types(_):
        return fuel_types

    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_weather_stations', mock_get_fire_weather_stations)
    monkeypatch.setattr(app.db.crud.hfi_calc, 'get_all_stations', mock_get_all_stations)
    # TODO: this is problematic, why are we calling get_fire_centre_stations twice?
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_centre_stations', mock_get_fire_centre_stations)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_centre_fire_start_ranges',
                        mock_get_fire_centre_fire_start_ranges)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fuel_types', mock_get_fuel_types)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_start_lookup', mock_get_fire_start_lookup)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fire_centre_stations', mock_get_fire_centre_stations)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fuel_type_by_id', mock_get_fuel_type_by_id)
    monkeypatch.setattr(app.routers.hfi_calc, 'crud_get_fuel_types', mock_get_fuel_types)


def _setup_mock_with_role(monkeypatch: pytest.MonkeyPatch, role: str):
    """ Prepare jwt decode to be mocked with permission
    """
    _setup_mock(monkeypatch)

    class MockJWTDecodeWithRole:
        """ Mock pyjwt module with role """

        def __init__(self, role):
            self.decoded_token = {
                "idir_username": "test_username",
                "client_roles": [
                    role
                ]}

        def __getitem__(self, key):
            return self.decoded_token[key]

        def get(self, key, _):
            "Returns the mock decoded token"
            return self.decoded_token[key]

        def decode(self):
            "Returns the mock decoded token"
            return self.decoded_token

    def mock_fire_start_role_function(*args, **kwargs):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole(role)

    if (role != 'None'):
        monkeypatch.setattr("jwt.decode", mock_fire_start_role_function)


headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer token'}


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
    response = client.post(url, headers=headers)
    return {
        'response': response
    }


@then(parsers.parse("request == saved = {request_saved}"), converters={'request_saved': strtobool})
def then_request_saved(spy_store_hfi_request: MagicMock, request_saved: bool):
    assert spy_store_hfi_request.called == request_saved
