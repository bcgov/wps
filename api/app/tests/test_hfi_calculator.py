""" BDD tests for API /hfi-calc/ """
import logging
import asyncio
from datetime import datetime
from os import name
from typing import List, Generator
from contextlib import contextmanager
import json
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import pytest
import app.main
from app.schemas.hfi_calc import WeatherStation, FireCentre, FuelType, PlanningArea, WeatherStationProperties
from app.tests.common import default_mock_client_get

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

    @contextmanager
    def mock_get_session_scope(*_) -> Generator[Session, None, None]:
        """ Slap some data into the database to match the query """
        kam_fire_centre = FireCentre(name='Kamloops Fire Centre')
        kam_pa = PlanningArea(name='Kamloops (K2)', fire_centre=kam_fire_centre)
        vernon_pa = PlanningArea(name='Vernon (K4)', fire_centre=kam_fire_centre)
        planning_areas = [kam_pa, vernon_pa]
        c7_fuel = FuelType(abbrev='C7', description='moo')
        o1b_fuel = FuelType(abbrev='O1B', description='meow')
        fuel_types = [c7_fuel, o1b_fuel]
        station_props_1 = WeatherStationProperties(
            name='AFTON', elevation=780, wfwx_station_uuid='dfasdf', fuel_type=o1b_fuel)
        station_props_2 = WeatherStationProperties(
            name='SALMON ARM', elevation=527, wfwx_station_uuid='asdfn', fuel_type=c7_fuel)
        station_1 = WeatherStation(code=322, station_props=station_props_1, planning_area=kam_pa)
        station_2 = WeatherStation(code=346, station_props=station_props_2, planning_area=vernon_pa)
        stations = [station_1, station_2]

        # Create a mock session - no filters, this is what you'll get on any query
        session = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(WeatherStation)], stations
            ),
            (
                [mock.call.query(FuelType)], fuel_types
            ),
            (
                [mock.call.query(FireCentre)], kam_fire_centre
            ),
            (
                [mock.call.query(PlanningArea)], planning_areas
            )
        ])
        yield session

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


@then('the station with index <index> has code <code>, named <station_name>, with fuel type <fuel_type> and elevation <elevation>, assigned to planning area <planning_area_name> and fire centre <fire_centre_name>')
def assert_individual_station_data(response, index, code, station_name, fuel_type, elevation, planning_area_name, fire_centre_name):
    """ Assert that the response includes specific data for an individual weather station """
    station = response.json(['stations'][index])
    assert station['code'] == code
    assert station['station_props']['name'] == station_name
    assert station['station_props']['fuel_type']['abbrev'] == fuel_type
    assert station['station_props']['elevation'] == elevation
    assert station['planning_area']['name'] == planning_area_name
    assert station['planning_area']['fire_centre']['name'] == fire_centre_name
