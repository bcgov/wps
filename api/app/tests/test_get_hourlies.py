""" BDD tests for API /hourlies. """
import logging
from datetime import datetime
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from aiohttp import ClientSession
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.main
import app.time_utils
from app.db.models import HourlyActual
from app.tests.common import default_mock_client_get
import app.wildfire_one

logger = logging.getLogger(__name__)


@scenario('test_get_hourlies.feature', 'Get hourlies',
          example_converters=dict(
              codes=str, status=int,
              num_groups=int,
              num_readings_per_group=str,
              use_wfwx=str))
def test_hourlies():
    """ BDD Scenario. """


# pylint: disable=unused-argument
@given('I request hourlies for stations: <codes> with <use_wfwx>')
def response(monkeypatch, mock_jwt_decode, codes, use_wfwx):
    """ Make /hourlies/ request using mocked out ClientSession.
    """

    # NOTE: should be using a converter
    # pylint: disable=eval-used
    stations = eval(codes)

    def mock_get_session(*args):
        """ Slap some actuals into the database to match the stations being queried """
        hourly_actuals = []
        for code in stations:
            hourly_actuals.append(HourlyActual(weather_date=datetime.fromisoformat(
                "2020-01-01T01:01+00:00"), station_code=code, temp_valid=True, temperature=11.1))

        # Create a mock session - no filters, this is what you'll get on any query
        session = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(HourlyActual)], hourly_actuals
            )
        ])
        return session

    if use_wfwx == 'True':
        logger.info('running test with WFWX set to True')
        monkeypatch.setenv("USE_WFWX", 'True')
        monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    else:
        logger.info('running test with WFWX set to False')
        monkeypatch.setenv("USE_WFWX", 'False')
        monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.post('/hourlies/', headers=headers, json={"stations": stations})


# pylint: disable=redefined-outer-name
@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('there are <num_groups> groups of hourlies')
def assert_number_of_hourlies_groups(response, num_groups):
    """ Assert that we receive the expected number of hourly groups """
    assert len(response.json()['hourlies']) == num_groups


@then('there are <num_readings_per_group> readings per group')
def assert_number_of_hourlies_per_group(response, num_readings_per_group):
    """ Assert that we receive the expected number of hourlies per groups """
    # pylint: disable=eval-used
    for index, item in enumerate(eval(num_readings_per_group)):
        assert len(response.json()['hourlies']
                   [index]['values']) == item
