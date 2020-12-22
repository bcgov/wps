""" BDD tests for API /noon_forecasts.
NOTE: This test currently only handles one station.
"""

import json
import os
import logging
from datetime import datetime
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

LOGGER = logging.getLogger(__name__)


@pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session """
    # pylint: disable=unused-argument
    def mock_get_session(*args):
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
        return session

    monkeypatch.setattr(app.db.database, 'get_read_session', mock_get_session)


@pytest.mark.usefixtures('mock_env_with_use_wfwx', 'mock_jwt_decode')
@scenario('test_noon_forecasts.feature', 'Get noon_forecasts',
          example_converters=dict(codes=str, status=int, num_groups=int))
def test_noon_forecasts():
    """ BDD Scenario. """


@given('I request noon_forecasts for stations: <codes>', target_fixture='response')
def given_request(monkeypatch, codes):
    """ Make /api/noon_forecasts/ request using mocked out ClientSession.
    """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    # NOTE: should be using a converter
    # pylint: disable=eval-used
    stations = eval(codes)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/api/noon_forecasts/', headers=headers, json={"stations": stations})


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('there are <num_groups> groups of forecasts')
def assert_number_of_forecasts_groups(response, num_groups):
    """ Assert that we receive the expected number of forecast groups """
    assert len(response.json()['noon_forecasts']) == num_groups
