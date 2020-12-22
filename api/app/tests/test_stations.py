""" Functional testing for API - stations using wf1 """
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from aiohttp import ClientSession
import pytest
from app.main import app
from app.tests.common import default_mock_client_get


@pytest.mark.usefixtures('mock_env_with_use_wfwx')
@scenario('test_stations.feature', 'Get weather stations from WFWX',
          example_converters=dict(status=int, index=int, code=int, name=str, lat=float,
                                  long=float, ecodivision_name=str, core_season=dict))
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


@then("there are active 16 weather stations")
def active_16_weather_stations(response):
    """ We expect there to be 16 weather stations. Even though we were given 50 stations from the
    API, some of those stations are inactive/invalid/disabled or don't have lat/long.
    """
    assert len(response.json()['weather_stations']) == 16


@then("there is a station in <index> has <code>, <name>, <lat> and <long>")
def there_is_a_station(response,  # pylint: too-many-arguments
                       index, code, name, lat, long):
    """ We expect a station to have a code, name, lat and long. """
    assert (response.json()['weather_stations'][index]['code'] == code and
            response.json()['weather_stations'][index]['name'] == name and
            response.json()['weather_stations'][index]['lat'] == lat and
            response.json()['weather_stations'][index]['long'] == long)


@then("the station has <ecodivision_name> with core_season <start_month> <start_day> - <end_month> <end_day>")
def station_ecodivision_data(response,  # pylint: too-many-arguments
                             index, ecodivision_name, start_month, start_day, end_month, end_day):
    """ We expect station's ecodivision to have name, start_month start_day - end_month end_day """
    assert (response.json()['weather_stations'][index]['ecodivision_name'] == ecodivision_name and
            response.json()['weather_stations'][index]['core_season'] == {
                "start_month": int(start_month),
                "start_day": int(start_day),
                "end_month": int(end_month),
                "end_day": int(end_day)})
