
from httpx import AsyncClient
from aiohttp import ClientSession
import pytest
import math
from app.fire_behaviour.cffdrs import CFFDRS
from app.tests.common import default_mock_client_get


firebat_url = '/api/fba-calc/stations'

CFFDRS.instance()


@pytest.fixture()
async def async_client():
    from app.main import app as test_app

    async with AsyncClient(app=test_app, base_url="https://test") as test_client:
        yield test_client


@pytest.mark.anyio
@pytest.mark.usefixtures('mock_jwt_decode')
async def test_m1_50conifer_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "M1",
                "crown_base_height": 6,
                "percentage_conifer": 50
            }
        ]
    })

    assert response.status_code == 200

    assert response.json()['stations'][0]['id'] == 0
    assert response.json()['stations'][0]['station_code'] == 230
    assert response.json()['stations'][0]['station_name'] == 'HORSEFLY'
    assert response.json()['stations'][0]['zone_code'] == 'C3'
    assert response.json()['stations'][0]['elevation'] == 701
    assert response.json()['stations'][0]['fuel_type'] == 'M1'

    assert math.isclose(response.json()['stations'][0]['fine_fuel_moisture_code'], 90.683, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['drought_code'], 340.544, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['initial_spread_index'], 7.51, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['build_up_index'], 117.899, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['duff_moisture_code'], 103.923, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['fire_weather_index'], 27.913, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['head_fire_intensity'], 4924.346, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['rate_of_spread'], 6.123, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['percentage_crown_fraction_burned'], 0.406, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['flame_length'], 4.052, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['sixty_minute_fire_size'], 4.628, abs_tol=0.1)
    assert math.isclose(response.json()['stations'][0]['thirty_minute_fire_size'], 0.548, abs_tol=0.001)

    assert response.json()['stations'][0]['fire_type'] == 'IC'
    assert response.json()['stations'][0]['critical_hours_hfi_4000'] == {"start": 15.0, "end": 19.0}
    assert response.json()['stations'][0]['critical_hours_hfi_10000'] is None