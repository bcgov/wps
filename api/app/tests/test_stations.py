""" Functional testing for API - stations using wf1 """
import json
from datetime import datetime, timezone
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import pytest
import app.main
from app.tests.common import default_mock_client_get
from app.tests import load_json_file, apply_crud_mapping


@scenario('test_stations.feature', 'Get weather stations')
def test_stations_scenario():
    """ BDD Scenario. """


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_stations.feature', 'Get detailed weather stations')
def test_detailed_stations_scenario():
    """ BDD Scenario. """


@given(parsers.parse("USE_WFWX={use_wfwx}"), converters=dict(use_wfwx=str))
def given_wfwx(monkeypatch, use_wfwx: str):
    """ Toggle between using wfwx or not """
    monkeypatch.setenv("USE_WFWX", use_wfwx)


@given(parsers.parse("utc_time: {utc_time}"), converters=dict(utc_time=int))
def given_utc_time(monkeypatch, utc_time: int):
    """ Mock out utc time """
    def mock_get_utc_now():
        return datetime.fromtimestamp(utc_time / 1000, tz=timezone.utc)
    monkeypatch.setattr(app.routers.stations, 'get_utc_now', mock_get_utc_now)


@given(parsers.parse("A crud mapping {crud_mapping}"),
       target_fixture='collector',
       converters=dict(crud_mapping=load_json_file(__file__)))
def given_a_crud_mapping(monkeypatch, crud_mapping: dict):
    """ Mock the sql response.
    """
    apply_crud_mapping(monkeypatch, crud_mapping, __file__)


@given(parsers.parse("I request a list of weather stations from {url} with {authentication}"),
       target_fixture='response', converters={'authentication': bool, 'url': str})
def given_request(monkeypatch, url: str, authentication: bool):
    """ Mock external requests and make GET /api/stations/ request """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    client = TestClient(app.main.app)
    if authentication:
        return dict(response=client.get(url, headers={'Authorization': 'Bearer token'}))
    return dict(response=client.get(url))


@then("there are at least 200 active weather stations")
def minimum_200_active_weather_stations(response):
    """ We expect there to be at least 200 active weather stations.
    """
    assert len(response['response'].json()['features']) >= 200


@then(parsers.parse("there is a station with {code}, {name}, {lat} and {long}"),
      converters=dict(code=int, name=str, lat=float, long=float))
def there_is_a_station(response, code, name, lat, long):  # pylint: disable=too-many-arguments
    """ We expect a station to have a code, name, lat and long. """
    station = next(x for x in response['response'].json()['features'] if x['properties']['code'] == code)

    assert station['properties']['code'] == code, "Code"
    assert station['properties']['name'] == name, "Name"
    assert station['geometry']['coordinates'][1] == lat, "Latitude"
    assert station['geometry']['coordinates'][0] == long, "Longitude"


@then(parsers.parse("the station has {ecodivision_name} with {core_season}"),
      converters=dict(ecodivision_name=str, core_season=json.loads))
def station_ecodivision_data(response, index, ecodivision_name, core_season: dict):
    """ We expect station's ecodivision to have name, start_month start_day - end_month end_day """
    data = response['response'].json()
    assert (data['features'][index]['properties']['ecodivision_name'] == ecodivision_name and
            data['features'][index]['properties']['core_season'] == core_season)


@ then(parsers.parse("the expected response is {expected_response}"),
       converters=dict(expected_response=load_json_file(__file__)))
def assert_expected_response(response, expected_response):
    """ We expect a certain response """
    assert response['response'].json() == expected_response
