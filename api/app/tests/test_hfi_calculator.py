""" BDD tests for API /hfi-calc/ """
import logging
from pytest_bdd import scenario, given, then
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from app.tests.common import default_mock_client_get
from app import wildfire_one
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
              danger_cl=int,
              fbp_fuel_type=str))
def test_hfi_planning_areas():
    """ BDD Scenario. """


@given('I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.', target_fixture='response')
def given_time_range_metrics_request(monkeypatch):
    """ Make /hfi-calc/daily request using mocked out ClientSession.
    """
    class AsyncIter:
        """Mock class for async iterators"""

        def __init__(self, items):
            self.items = items

        async def __aiter__(self):
            for item in self.items:
                yield item

    raw_response = AsyncIter([{'stationCode': 322,
                               'temperature': 1,
                               'relativeHumdity': 1,
                               'windSpeed': 1,
                               'windDirection': 1,
                               'precipitation': 1,
                               'grasslandCuring': 1,
                               'fineFuelMoistureCode': 1,
                               'duffMoistureCode': 1,
                               'droughtCode': 1,
                               'initialSpreadIndex': 1,
                               'fireWeatherIndex': 1,
                               'buildUpIndex': 1,
                               'dailySeverityRating': 1,
                               "recordType": {
                                   "id": "ACTUAL",
                                   "displayLabel": "Actual",
                                   "displayOrder": 1,
                                   "createdBy": "DATA_LOAD",
                                   "lastModifiedBy": "DATA_LOAD"
                               },
                               'fbpFuelType': "TBD",
                               'observationValidInd': True,
                               'observationValidComment': ""
                               }])

    def mock_paged_response_generator(*_):
        """Mock out the paged response from WFWX"""
        return raw_response

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(wildfire_one, '_fetch_paged_response_generator', mock_paged_response_generator)
    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return client.get('/api/hfi-calc/daily', headers=headers)


@then('the response status code is <status_code>')
def assert_status_code(response, status_code: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == int(status_code)

# pylint: disable=invalid-name, too-many-arguments, line-too-long, too-many-locals


@then('the station with status <status>has code <code>, named <station_name>, with fuel type <fuel_type> and elevation <elevation>, assigned to planning area <planning_area_name> and fire centre <fire_centre_name>')
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
    dailies = response.json(['dailies'])
    assert dailies['temperature'] == temperature
    assert dailies['relative_humidity'] == relative_humidity
    assert dailies['wind_direction'] == wind_direction
    assert dailies['wind_speed'] == wind_speed
    assert dailies['precipitation'] == precipitation
    assert dailies['grass_cure_percentage'] == grass_cure_percentage
    assert dailies['ffmc'] == ffmc
    assert dailies['dmc'] == dmc
    assert dailies['dc'] == dc
    assert dailies['isi'] == isi
    assert dailies['bui'] == bui
    assert dailies['fwi'] == fwi
    assert dailies['danger_cl'] == danger_cl
    assert dailies['fbp_fuel_type'] == fbp_fuel_type
