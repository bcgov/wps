""" Functional testing for API - stations using wf1 """
import json
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import pytest
from app.main import app
from app.tests.common import default_mock_client_get


@pytest.mark.usefixtures('mock_env_with_use_wfwx')
@scenario('test_stations.feature', 'Get weather stations from WFWX',
          example_converters=dict(status=int, index=int, code=int, name=str, lat=float,
                                  long=float, ecodivision_name=str, core_season=json.loads))
def test_stations_scenario():
    """ BDD Scenario. """


@given("I request a list of weather stations", target_fixture='response')
def given_request(monkeypatch):
    """ Mock external requests and make GET /api/stations/ request """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    client = TestClient(app)
    return client.get('/api/stations/')


@then("the response status code is <status>")
def status_code(response, status: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then("there are at least 200 active weather stations")
def minimum_200_active_weather_stations(response):
    """ We expect there to be at least 200 active weather stations.
    """
    assert len(response.json()['features']) >= 200


@then("there is a station in <index> has <code>, <name>, <lat> and <long>")
def there_is_a_station(response, index, code, name, lat, long):  # pylint: disable=too-many-arguments
    """ We expect a station to have a code, name, lat and long. """
    assert (response.json()['features'][index]['properties']['code'] == code and
            response.json()['features'][index]['properties']['name'] == name and
            response.json()['features'][index]['geometry']['coordinates'][1] == lat and
            response.json()['features'][index]['geometry']['coordinates'][0] == long)


@then("the station has <ecodivision_name> with <core_season>")
def station_ecodivision_data(response, index, ecodivision_name, core_season: dict):
    """ We expect station's ecodivision to have name, start_month start_day - end_month end_day """
    assert (response.json()['features'][index]['properties']['ecodivision_name'] == ecodivision_name and
            response.json()['features'][index]['properties']['core_season'] == core_season)
