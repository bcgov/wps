""" BDD tests for API /hourlies. """
import logging
from datetime import datetime, timezone
from pytest_bdd import scenario, given, then
from starlette.testclient import TestClient
from aiohttp import ClientSession
import app.main
import app.time_utils
from app.tests.common import default_mock_client_get
import app.wildfire_one

LOGGER = logging.getLogger(__name__)


@scenario('test_get_hourlies.feature', 'Get hourlies',
          example_converters=dict(codes=str, status=int, num_groups=int, num_readings_per_group=str))
def test_hourlies():
    """ BDD Scenario. """


# pylint: disable=unused-argument
@given('I request hourlies for stations: <codes>')
def response(monkeypatch, mock_env_with_use_wfwx, mock_jwt_decode, codes):
    """ Make /hourlies/ request using mocked out ClientSession.
    """

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    # NOTE: should be using a converter
    # pylint: disable=eval-used
    stations = eval(codes)

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
