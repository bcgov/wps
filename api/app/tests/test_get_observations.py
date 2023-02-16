""" BDD tests for API /hourlies. """
import logging
import asyncio
from datetime import datetime
import json
from typing import List
from pytest_bdd import scenario, given, then, parsers
from starlette.testclient import TestClient
from aiohttp import ClientSession
from sqlalchemy.orm import Session
import pytest
import app.main
import app.utils.time
from app.db.models.observations import HourlyActual
from app.schemas.stations import WeatherStation
from app.tests.common import default_mock_client_get
import app.wildfire_one.wfwx_api
from app.utils import strtobool

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_get_observations.feature', 'Get hourly observations')
def test_hourlies():
    """ BDD Scenario. """


@given(parsers.parse('I request hourlies for stations: {codes} with {use_wfwx} and {mock_redis_exception}'),
       target_fixture='response',
       converters={'codes': json.loads, 'use_wfwx': strtobool, 'mock_redis_exception': strtobool})
def given_hourlies_request(monkeypatch, codes: List, use_wfwx: bool, mock_redis_exception: bool):
    """ Make /observations/ request using mocked out ClientSession.
    """

    def build_mock_stations(codes: List):
        stations = []
        for code in codes:
            station = WeatherStation(code=code, name="one", lat=0, long=0)
            stations.append(station)
        result = asyncio.Future()
        result.set_result(stations)
        return result

    def mock_get_hourly_actuals(
            session: Session,
            station_codes: List[int],
            start_date: datetime,
            end_date: datetime = None):
        """ Mock the get_hourly_actuals function. """
        hourly_actuals = []
        for code in codes:
            hourly_actuals.append(HourlyActual(weather_date=datetime.fromisoformat(
                "2020-01-01T01:01+00:00"), station_code=code, temp_valid=True, temperature=11.1))
        return hourly_actuals

    class MockRedis():
        """ Mock class"""

        def get(self, *args, **kwargs):
            """ Mock function """
            if mock_redis_exception:
                raise Exception('explode')
            return {}

        def set(self, *args, **kwargs):
            """ Mock function """
            if mock_redis_exception:
                raise Exception('explode')

    def mock_create_redis():
        """ function to mock out creation of redis"""
        return MockRedis()

    # mock out redis:
    monkeypatch.setattr(app.data.ecodivision_seasons, 'create_redis', mock_create_redis)

    if use_wfwx:
        logger.info('running test with WFWX set to True')
        monkeypatch.setenv("USE_WFWX", 'True')
        monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    else:
        logger.info('running test with WFWX set to False')
        monkeypatch.setenv("USE_WFWX", 'False')
        monkeypatch.setattr('app.wildfire_one.wfwx_api.get_stations_by_codes',
                            lambda _: build_mock_stations(codes))
        monkeypatch.setattr('app.hourlies.get_hourly_actuals', mock_get_hourly_actuals)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return dict(response=client.post('/api/observations/', headers=headers, json={"stations": codes}))


@then(parsers.parse('there are {num_groups} groups of hourlies'), converters={'num_groups': int})
def assert_number_of_hourlies_groups(response, num_groups: int):
    """ Assert that we receive the expected number of hourly groups """
    assert len(response['response'].json()['hourlies']) == num_groups


@then(parsers.parse('there are {num_readings_per_group} readings per group'),
      converters={'num_readings_per_group': json.loads})
def assert_number_of_hourlies_per_group(
        response,
        num_readings_per_group: List):
    """ Assert that we receive the expected number of hourlies per groups """
    for index, item in enumerate(num_readings_per_group):
        assert len(response['response'].json()['hourlies']
                   [index]['values']) == item
