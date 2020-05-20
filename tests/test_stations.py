""" Functional testing for API - stations using wf1 """
import json
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from main import APP
from tests.common import MockClientSession

# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments


@scenario('test_stations.feature', 'Get weather stations from WFWX',
          example_converters=dict(status=int, index=int, code=int, name=str, lat=float, long=float))
def test_stations_scenario():
    """ BDD Scenario. """


@given("I request a list of weather stations")
def response(monkeypatch, mock_env_with_use_wfwx):
    """ Mock external requests and make GET /stations/ request """

    def mock_client_get(*args, **kwargs):
        url = args[1]
        if '/token' in url:
            return MockClientSession(json={'access_token': 'Bearer token'})

        if '/page/v1/stations?' in url:
            match = url.find('page=')
            with open('tests/wf1_stations_page{}.json'.format(url[match+5:match+6])) as page:
                return MockClientSession(json=json.load(page))

        raise Exception('unexpected url: {}'.format(url))

    monkeypatch.setattr(ClientSession, 'get', mock_client_get)

    client = TestClient(APP)
    return client.get('/stations/')


@then("the response status code is <status>")
def status_code(response, status: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then("there are active 16 weather stations")
def active_16_weather_stations(response):
    """ We expect there to be 16 weather stations. Even though we were given 50 stations from the
    API, some of those stations are inactive/invalid/disabled or don't have lat/long.
    """
    assert len(response.json()['weather_stations']) == 16


@then("there is a station in <index> has <code>, <name>, <lat>, and <long>")
def there_is_a_station(response, index, code, name, lat, long):
    """ We expect a station to have a code, name, lat and long. """
    assert response.json()['weather_stations'][index] == {
        "code": code,
        "name": name,
        "lat": lat,
        "long": long
    }
