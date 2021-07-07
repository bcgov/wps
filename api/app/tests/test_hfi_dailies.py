""" BDD tests for API /hfi-calc/daily """
import logging
from pytest_bdd import scenario, given, then
import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient
from pytest_mock import MockerFixture
from app.tests.common import default_mock_client_get
from app.wildfire_one.wfwx_api import WFWXWeatherStation
import app.main

logger = logging.getLogger(__name__)


class AsyncIter:
    """ Async itereable use for mocking out raw dailies."""

    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_hfi_dailies.feature', 'Get metrics for stations',
          example_converters=dict(
              code=int,
              status=str,
              temperatire=float,
              relative_humidity=float,
              wind_speed=float,
              wind_direction=float,
              grass_cure_percentage=float,
              precipitation=float,
              ffmc=float,
              dmc=float,
              dc=float,
              isi=float,
              bui=float,
              fwi=float,
              danger_cl=float,
              fbp_fuel_type=str))
def test_hfi_daily_metrics():
    """ BDD Scenario. """


@given('I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.', target_fixture='response')  # pylint: disable=line-too-long
def given_time_range_metrics_request(monkeypatch, mocker: MockerFixture, mock_cffdrs):  # pylint: disable=unused-argument
    """ Make /hfi-calc/daily request using mocked out ClientSession.
    """

    mocker.patch('app.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes',
                 return_value=[WFWXWeatherStation(
                     wfwx_id='1', code=322, name='test', latitude=1, longitude=1, elevation=1)])
    mocker.patch('app.wildfire_one.wfwx_api.fetch_paged_response_generator',
                 return_value=AsyncIter([{'stationCode': 322,
                                          "stationId": '1',
                                          "initialSpreadIndex": 1,
                                          "buildUpIndex": 1,
                                          "fineFuelMoistureCode": 1,
                                          "recordType": {"id": "ACTUAL"},
                                          "temperature": 1.0,
                                          "relativeHumidity": 1.0,
                                          "windSpeed": 1.0,
                                          "windDirection": 1.0,
                                          "precipitation": 1.0,
                                          "grasslandCuring": 1.0,
                                          "dailySeverityRating": 1.0,
                                          "droughtCode": 1.0,
                                          "duffMoistureCode": 1.0,
                                          "fireWeatherIndex": 1.0
                                          }]))

    # To build generic objects with attributes
    object_builder = lambda **kwargs: type("Object", (), kwargs)()
    planning_station = object_builder(station_code=322)
    fuel_type = object_builder(abbrev="C7")
    mocker.patch('app.db.crud.hfi_calc.get_stations_with_fuel_types',
                 return_value=[(planning_station, fuel_type)])
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    return client.get('/api/hfi-calc/daily', headers=headers)


@then('the response status code is <status_code>')
def assert_status_code_200(response, status_code: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == int(status_code)


@then('the response has status <status>')
def assert_status(response, status):
    """ Assert expected status """
    assert status == response.json()['dailies'][0]['status']


@then('<temperature>')
def assert_temperature(response, temperature):
    """ Assert expected temperature """
    assert float(temperature) == response.json()['dailies'][0]['temperature']


@then('<relative_humidity>')
def assert_relative_humidity(response, relative_humidity):
    """ Assert expected relative_humidity """
    assert relative_humidity == response.json()['dailies'][0]['relative_humidity']


@then('<wind_direction>')
def assert_wind_direction(response, wind_direction):
    """ Assert expected wind_direction """
    assert wind_direction == response.json()['dailies'][0]['wind_direction']


@then('<wind_speed>')
def assert_wind_speed(response, wind_speed):
    """ Assert expected wind_speed """
    assert wind_speed == response.json()['dailies'][0]['wind_speed']


@then('<precipitation>')
def assert_precipitation(response, precipitation):
    """ Assert expected precipitation """
    assert precipitation == response.json()['dailies'][0]['precipitation']


@then('<grass_cure_percentage>')
def assert_grass_cure_percentage(response, grass_cure_percentage):
    """ Assert expected grass_cure_percentage """
    assert grass_cure_percentage == response.json()['dailies'][0]['grass_cure_percentage']


@then('<ffmc>')
def assert_ffmc(response, ffmc):
    """ Assert expected ffmc """
    assert ffmc == response.json()['dailies'][0]['ffmc']

# pylint: disable= invalid-name


@then('<dc>')
def assert_dc(response, dc):
    """ Assert expected dc """
    assert dc == response.json()['dailies'][0]['dc']


@then('<dmc>')
def assert_dmc(response, dmc):
    """ Assert expected dmc """
    assert dmc == response.json()['dailies'][0]['dmc']


@then('<isi>')
def assert_isi(response, isi):
    """ Assert expected isi """
    assert isi == response.json()['dailies'][0]['isi']


@then('<bui>')
def assert_bui(response, bui):
    """ Assert expected bui """
    assert bui == response.json()['dailies'][0]['bui']


@then('<fwi>')
def assert_fwi(response, fwi):
    """ Assert expected fwi """
    assert fwi == response.json()['dailies'][0]['fwi']


@then('<danger_class>')
def assert_danger_class(response, danger_class):
    """ Assert expected danger_class """
    assert float(danger_class) == response.json()['dailies'][0]['danger_class']
