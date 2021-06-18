""" BDD tests for API /hfi-calc/ """
import logging
from pytest_bdd import scenario, given, then
import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient
from app.tests.common import default_mock_client_get
import app.main

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_hfi_calculator.feature', 'Get metrics for stations',
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

# pylint: disable=line-too-long


@given('I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp> .', target_fixture='response')
def given_time_range_metrics_request(monkeypatch):
    """ Make /hfi-calc/daily request using mocked out ClientSession.
    """

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

# pylint: disable=invalid-name, too-many-arguments, line-too-long, too-many-locals


@then('the status <status> , with temperature <temperature> and relative humidity <relative_humidity>, and wind_direction <wind_direction> and wind_speed <wind_speed> and precipitation <precipitation> and grass_cure_percentage <grass_cure_percentage> and ffmc <ffmc> and dc <dc> and <dmc> and isi <isi> and <bui> and fwi <fwi> and danger_cl <danger_cl> and fbp_fuel_type <fbp_fuel_type>')
def assert_individual_station_data(
        response,
        temperature,
        relative_humidity,
        wind_direction,
        wind_speed,
        precipitation,
        grass_cure_percentage,
        ffmc,
        dc,
        dmc,
        isi,
        bui,
        fwi,
        danger_cl,
        fbp_fuel_type):
    """ Assert that the response includes specific data for an individual weather station """
    daily = response.json()['dailies'][0]
    assert daily['temperature'] == float(temperature)
    assert daily['relative_humidity'] == float(relative_humidity)
    assert daily['wind_direction'] == float(wind_direction)
    assert daily['wind_speed'] == float(wind_speed)
    assert daily['precipitation'] == float(precipitation)
    assert daily['grass_cure_percentage'] == float(grass_cure_percentage)
    assert daily['ffmc'] == float(ffmc)
    assert daily['dmc'] == float(dmc)
    assert daily['dc'] == float(dc)
    assert daily['isi'] == float(isi)
    assert daily['bui'] == float(bui)
    assert daily['fwi'] == float(fwi)
    assert daily['danger_cl'] == float(danger_cl)
    assert daily['fbp_fuel_type'] == fbp_fuel_type
