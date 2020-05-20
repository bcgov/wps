""" Functional testing for /forecasts/ endpoint.
"""
import logging
from datetime import datetime
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import numpy
from main import APP
from tests.common import MockClientSession

LOGGER = logging.getLogger(__name__)

# pylint: disable=unused-argument, redefined-outer-name, eval-used


@scenario("test_forecasts.feature", "Get forecasts from spotwx",
          example_converters=dict(codes=str, status=int, num_forecasts=int))
def test_forecasts_scenario():
    """ BDD Scenario. """


@given("I request weather forecasts for stations: <codes>")
def response(monkeypatch, mock_jwt_decode, codes):
    """ Mock external requests and make GET /forecasts/ request """

    def mock_client_get(*args, **kwargs):
        url = args[1]
        if 'spotwx' in url:
            with open('tests/spotwx_response_sample.csv', mode='r') as spotwx:
                data = spotwx.read()
                return MockClientSession(text=data)

        raise Exception('unexpected url: {}'.format(url))

    monkeypatch.setattr(ClientSession, 'get', mock_client_get)

    client = TestClient(APP)
    stations = eval(codes)
    return client.post('/forecasts/', headers={'Authorization': "Bearer token"}, json={"stations": stations})


@then("the response status code is <status>")
def status_code(response, status: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then("there are <num_forecasts> from two stations")
def num_of_forecasts(response, num_forecasts):
    """ Assert that we receive the corrent number of forecast """
    assert len(response.json()['forecasts']) == num_forecasts


@then("there are 10 days of forecasts for each station")
def ten_days_of_forecasts(response):
    """ We're expecting a 10 day forecast. """
    assert len(response.json()['forecasts'][0]['values']) == 10


@then("forecasts have noon values only")
def expect_noon_values_only(response):
    """ We're expecting noon values (20h00 UTC). """
    for forecast in response.json()['forecasts']:
        for values in forecast['values']:
            timestamp = datetime.fromisoformat(values['datetime'])
            assert timestamp.hour == 20


@then("forecast values should be interpolated")
def expect_interpolated_values(response):
    """ We're expecting interpolated values, so we check on of the calculations. """
    # dates matching csv file:
    x_p = [datetime.fromisoformat('2020-05-04T18:00:00').timestamp(),
           datetime.fromisoformat('2020-05-04T21:00:00').timestamp()]
    # temperatures matching csv file:
    f_p = [8.7, 12.1]
    # calculate interpolated temperature
    expected_temperature = numpy.interp(datetime.fromisoformat(
        '2020-05-04T20:00:00').timestamp(), x_p, f_p)
    temp_value = response.json()['forecasts'][0]['values'][0]['temperature']
    assert temp_value == expected_temperature
