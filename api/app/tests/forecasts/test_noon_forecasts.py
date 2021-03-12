""" BDD tests for API /noon_forecasts.
NOTE: This test currently only handles one station.
"""

import json
import os
import logging
from contextlib import contextmanager
from typing import List, Generator
from datetime import datetime
from sqlalchemy.orm import Session
import pytest
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from aiohttp import ClientSession
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.main
from app.tests.common import default_mock_client_get
import app.wildfire_one
import app.db.database
from app.db.models.forecasts import NoonForecast

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session """
    # pylint: disable=unused-argument
    @contextmanager
    def mock_get_session_scope(*args) -> Generator[Session, None, None]:
        session = UnifiedAlchemyMagicMock()
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, 'test_noon_forecasts.json')
        with open(filename) as data:
            json_data = json.load(data)
            for forecast in json_data:
                forecast['weather_date'] = datetime.fromisoformat(
                    forecast['weather_date'])
                forecast['created_at'] = datetime.fromisoformat(
                    forecast['created_at'])
                session.add(NoonForecast(**forecast))
        yield session

    monkeypatch.setattr(app.db.database, 'get_read_session_scope', mock_get_session_scope)


@pytest.mark.usefixtures('mock_env_with_use_wfwx', 'mock_jwt_decode')
@scenario('test_noon_forecasts.feature', 'Get noon_forecasts',
          example_converters=dict(codes=json.loads, status=int, num_groups=int))
def test_noon_forecasts():
    """ BDD Scenario. """


@given('I request noon_forecasts for stations: <codes>', target_fixture='response')
def given_request(monkeypatch, codes: List):
    """ Make /api/forecasts/noon/ request using mocked out ClientSession.
    """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/api/forecasts/noon/', headers=headers, json={"stations": codes})


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('there are <num_groups> groups of forecasts')
def assert_number_of_forecasts_groups(response, num_groups):
    """ Assert that we receive the expected number of forecast groups """
    assert len(response.json()['noon_forecasts']) == num_groups
