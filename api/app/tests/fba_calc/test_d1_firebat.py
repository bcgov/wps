
from httpx import AsyncClient
from aiohttp import ClientSession
import pytest
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
async def test_d1_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "D1"
            }
        ]
    })

    assert response.status_code == 200
    assert response.json() == {
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "station_name": "HORSEFLY",
                "zone_code": "C3",
                "elevation": 701,
                "fuel_type": "D1",
                "status": "ACTUAL",
                "temp": 25.2,
                "rh": 31.0,
                "wind_direction": 282,
                "wind_speed": 9.2,
                "precipitation": 0.0,
                "grass_cure": None,
                "fine_fuel_moisture_code": 90.683,
                "drought_code": 340.544,
                "initial_spread_index": 7.51,
                "build_up_index": 117.899,
                "duff_moisture_code": 103.923,
                "fire_weather_index": 27.915,
                "head_fire_intensity": 716.58,
                "rate_of_spread": 1.8,
                "fire_type": "SUR",
                "percentage_crown_fraction_burned": 0.0,
                "flame_length": 1.546,
                "sixty_minute_fire_size": 0.74,
                "thirty_minute_fire_size": 0.132,
                "critical_hours_hfi_4000": None,
                "critical_hours_hfi_10000": None
            }
        ]
    }