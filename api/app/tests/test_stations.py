""" Functional testing for API - stations using wf1 """
import json
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import pytest
from app.main import app
from app.tests.common import default_mock_client_get
from app.tests import load_json_file


@scenario('test_stations.feature', 'Get weather stations',
          example_converters=dict(status=int, index=int, code=int, name=str, lat=float,
                                  long=float, use_wfwx=str, url=str, ecodivision_name=str, core_season=json.loads))
def test_stations_scenario():
    """ BDD Scenario. """


@scenario('test_stations.feature', 'Get detailed weather stations',
          example_converters=dict(status=int, use_wfwx=str, url=str, expected_response=load_json_file(__file__)))
def test_detailed_stations_scenario():
    """ BDD Scenario. """


@given("USE_WFWX=<use_wfwx>")
def given_wfwx(monkeypatch, use_wfwx: str):
    """ Toggle between using wfwx or not """
    monkeypatch.setenv("USE_WFWX", use_wfwx)


@given("I request a list of weather stations from <url>", target_fixture='response')
def given_request(monkeypatch, url: str):
    """ Mock external requests and make GET /api/stations/ request """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    client = TestClient(app)
    return client.get(url)


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


@then("the expected response is <expected_response>")
def assert_expected_response(response, expected_response):
    """ We expect a certain response """
    # with open('actual_tmp.json', 'w') as f:
    #     json.dump(response.json(), f, indent=4)
    assert response.json() == expected_response
