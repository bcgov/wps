
from httpx import AsyncClient
from aiohttp import ClientSession
import pytest
import math
from app.fire_behaviour.cffdrs import CFFDRS
from wps_shared.tests.common import default_mock_client_get


firebat_url = '/api/fba-calc/stations'

CFFDRS.instance()


@pytest.fixture()
async def async_client():
    from app.main import app as test_app

    async with AsyncClient(app=test_app, base_url="https://test") as test_client:
        yield test_client


@pytest.mark.anyio
@pytest.mark.usefixtures('mock_jwt_decode')
async def test_01a_90curing_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-06",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "O1A",
                "grass_cure": "90"
            }
        ]
    })

    assert response.status_code == 200

    assert response.json()['stations'][0]['id'] == 0
    assert response.json()['stations'][0]['station_code'] == 230
    assert response.json()['stations'][0]['station_name'] == 'HORSEFLY'
    assert response.json()['stations'][0]['zone_code'] == 'C3'
    assert response.json()['stations'][0]['elevation'] == 701
    assert response.json()['stations'][0]['fuel_type'] == 'O1A'
    assert response.json()['stations'][0]['grass_cure'] == 90.0

    assert math.isclose(response.json()['stations'][0]['fine_fuel_moisture_code'], 93.258, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['drought_code'], 340.544, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['initial_spread_index'], 10.810, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['build_up_index'], 117.899, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['duff_moisture_code'], 103.923, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['fire_weather_index'], 35.640, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['head_fire_intensity'], 2749.522, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['rate_of_spread'], 26.186, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['percentage_crown_fraction_burned'], 0.0, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['flame_length'], 3.027, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['sixty_minute_fire_size'], 79.408, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['thirty_minute_fire_size'], 14.343, abs_tol=0.001)

    assert response.json()['stations'][0]['fire_type'] == 'SUR'
    assert response.json()['stations'][0]['critical_hours_hfi_4000'] is None
    assert response.json()['stations'][0]['critical_hours_hfi_10000'] is None
