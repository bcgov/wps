""" BDD tests for API /hourlies. """
import logging
import asyncio
from datetime import datetime
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
import app.utils.time
from app.db.models.observations import HourlyActual
from app.schemas.stations import WeatherStation
from app.tests.common import default_mock_client_get
import app.wildfire_one

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_get_observations.feature', 'Get hourly observations',
          example_converters=dict(
              codes=json.loads, status=int,
              num_groups=int,
              num_readings_per_group=json.loads,
              use_wfwx=str))
def test_hourlies():
    """ BDD Scenario. """


@given('I request hourlies for stations: <codes> with <use_wfwx>', target_fixture='response')
def given_hourlies_request(monkeypatch, codes: List, use_wfwx):
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

    @contextmanager
    def mock_get_session_scope(*_) -> Generator[Session, None, None]:
        """ Slap some actuals into the database to match the stations being queried """
        hourly_actuals = []
        for code in codes:
            hourly_actuals.append(HourlyActual(weather_date=datetime.fromisoformat(
                "2020-01-01T01:01+00:00"), station_code=code, temp_valid=True, temperature=11.1))

        # Create a mock session - no filters, this is what you'll get on any query
        session = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(HourlyActual)], hourly_actuals
            )
        ])
        yield session

    if use_wfwx == 'True':
        logger.info('running test with WFWX set to True')
        monkeypatch.setenv("USE_WFWX", 'True')
        monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    else:
        logger.info('running test with WFWX set to False')
        monkeypatch.setenv("USE_WFWX", 'False')
        monkeypatch.setattr('app.wildfire_one.get_stations_by_codes', lambda _: build_mock_stations(codes))
        monkeypatch.setattr(
            app.db.database, 'get_read_session_scope', mock_get_session_scope)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/api/observations/', headers=headers, json={"stations": codes})


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('there are <num_groups> groups of hourlies')
def assert_number_of_hourlies_groups(response, num_groups):
    """ Assert that we receive the expected number of hourly groups """
    assert len(response.json()['hourlies']) == num_groups


@then('there are <num_readings_per_group> readings per group')
def assert_number_of_hourlies_per_group(
        response,
        num_readings_per_group: List):
    """ Assert that we receive the expected number of hourlies per groups """
    for index, item in enumerate(num_readings_per_group):
        assert len(response.json()['hourlies']
                   [index]['values']) == item
