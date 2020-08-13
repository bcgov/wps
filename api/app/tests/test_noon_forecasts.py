""" BDD tests for API /noon_forecasts.
NOTE: This test currently only handles one station.
"""

import json
import os
import logging
from datetime import datetime
import pytz
import pytest
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from aiohttp import ClientSession
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.main
from app.tests.common import default_mock_client_get
import app.wildfire_one
import app.db.database
from app.db.models import NoonForecasts

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
                session.add(NoonForecasts(**forecast))
        return session

    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)


@scenario('test_noon_forecasts.feature', 'Get noon_forecasts',
          example_converters=dict(codes=str, status=int, num_groups=int))
def test_noon_forecasts():
    """ BDD Scenario. """


# pylint: disable=unused-argument, redefined-outer-name
@given('I request noon_forecasts for stations: <codes>')
def response(monkeypatch, mock_env_with_use_wfwx, mock_jwt_decode, codes):
    """ Make /noon_forecasts/ request using mocked out ClientSession.
    """

    # Mock out the part that gives us a datetime.
    # pylint: disable=unused-argument
    def mock_now(*args, **kwargs):
        return datetime.fromtimestamp(1590076213962/1000, tz=pytz.utc)

    monkeypatch.setattr(app.wildfire_one, '_get_now', mock_now)
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    # NOTE: should be using a converter
    # pylint: disable=eval-used
    stations = eval(codes)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/noon_forecasts/', headers=headers, json={"stations": stations})


# pylint: disable=redefined-outer-name
@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we recieve the expected status code """
    assert response.status_code == status


@then('there are <num_groups> groups of forecasts')
def assert_number_of_forecasts_groups(response, num_groups):
    """ Assert that we recieve the expected number of forecast groups """
    print(response.json())
    assert len(response.json()['noon_forecasts']) == num_groups
