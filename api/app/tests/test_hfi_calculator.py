""" BDD tests for API /hfi-calc/ """
import logging
from aiohttp.client import ClientSession
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from app.db.models.hfi_calc import PlanningWeatherStation, FireCentre, FuelType, PlanningArea
import app.main
from app.tests.common import default_mock_client_get
import app.routers.hfi_calc

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_hfi_calculator.feature', 'Get fire centres, planning areas, and weather stations',
          example_converters=dict(
              status=int,
              num_weather_stations=int,
              index=int,
              code=int,
              station_name=str,
              fuel_type=str,
              elevation=int))
def test_hfi_planning_areas():
    """ BDD Scenario. """


@given('I request all fire centres, planning areas, etc.', target_fixture='response')
def given_hfi_planning_areas_request(monkeypatch):
    """ Make /hfi-calc/ request using mocked out ClientSession.
    """

    def mock_get_planning_weather_stations(*_, **__):
        return [
            PlanningWeatherStation(station_code=322, fuel_type_id=1, planning_area_id=1),
            PlanningWeatherStation(station_code=346, fuel_type_id=2, planning_area_id=2),
            PlanningWeatherStation(station_code=334, fuel_type_id=2, planning_area_id=2)
        ]

    def mock_get_fuel_type_by_id(_: Session, fuel_type_id: int):
        if fuel_type_id == 1:
            return FuelType(abbrev='O1B', description='neigh')
        if fuel_type_id == 2:
            return FuelType(abbrev='C7', description='moo')
        return None

    def mock_get_fire_centre_by_id(*_, **__):
        return FireCentre(name='Kamloops Fire Centre')

    def mock_get_planning_area_by_id(_: Session, planning_area_id: int):
        if planning_area_id == 1:
            return PlanningArea(name='Kamloops (K2)', fire_centre_id=1)
        if planning_area_id == 2:
            return PlanningArea(name='Vernon (K4)', fire_centre_id=1)
        return None

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fuel_type_by_id', mock_get_fuel_type_by_id)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_planning_area_by_id', mock_get_planning_area_by_id)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fire_centre_by_id', mock_get_fire_centre_by_id)
    monkeypatch.setattr(
        app.routers.hfi_calc, 'get_planning_weather_stations', mock_get_planning_weather_stations)

    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.get('/api/hfi-calc/', headers=headers)


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('there are at least <num_weather_stations> weather stations')
def assert_number_of_weather_stations(response, num_weather_stations):
    """ Assert that we receive the minimum expected number of weather stations """
    assert len(response.json()['stations']) >= num_weather_stations


@then('the station with index <index> has code <code>, named <station_name>, with fuel type <fuel_type> and '
      'elevation <elevation>, assigned to planning area <planning_area_name> and fire centre '
      '<fire_centre_name>')
# pylint: disable=too-many-arguments
def assert_individual_station_data(response, index, code, station_name, fuel_type, elevation,
                                   planning_area_name, fire_centre_name):
    """ Assert that the response includes specific data for an individual weather station """
    station = response.json()['stations'][index]
    assert station['code'] == code
    assert station['station_props']['name'] == station_name
    assert station['station_props']['fuel_type']['abbrev'] == fuel_type
    assert station['station_props']['elevation'] == elevation
    assert station['planning_area']['name'] == planning_area_name
    assert station['planning_area']['fire_centre']['name'] == fire_centre_name
