""" BDD tests for API /hfi-calc/ """
from pytest_bdd import scenario, given, then
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from app.tests.common import default_mock_client_get
import app.main
from app.db.models.hfi_calc import PlanningWeatherStation, FireCentre, FuelType, PlanningArea
import app.routers.hfi_calc


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_fba_endpoint.feature', 'Get fire centres with their stations',
          example_converters=dict(
              status=int,
              num_fire_centres=int))
def test_fba_fire_centers():
    """ BDD Scenario. """


@given('I request all fire centres', target_fixture='response')
def given_fba_fire_centers_request(monkeypatch):
    """ Make /fba/ request using mocked out ClientSession.
    """

    def mock_get_fire_weather_stations(_: Session):
        fire_centre = FireCentre(name='Kamloops Fire Centre')
        planning_area_1 = PlanningArea(name='Kamloops (K2)', fire_centre_id=1)
        planning_area_2 = PlanningArea(name='Vernon (K4)', fire_centre_id=1)
        fuel_type_1 = FuelType(abbrev='O1B', description='neigh')
        fuel_type_2 = FuelType(abbrev='C7', description='moo')
        return (
            (PlanningWeatherStation(station_code=322, fuel_type_id=1,
             planning_area_id=1), fuel_type_1, planning_area_1, fire_centre),
            (PlanningWeatherStation(station_code=346, fuel_type_id=2,
             planning_area_id=2), fuel_type_2, planning_area_2, fire_centre),
            (PlanningWeatherStation(station_code=334, fuel_type_id=2,
             planning_area_id=2), fuel_type_2, planning_area_2, fire_centre)
        )

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fire_weather_stations', mock_get_fire_weather_stations)

    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    return client.get('/api/hfi-calc/fire-centres/', headers=headers)


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status
