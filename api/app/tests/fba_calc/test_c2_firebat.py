
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
async def test_c2_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "C2",
                "crown_base_height": 3,
                "percentage_conifer": 100
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
                "fuel_type": "C2",
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
                "head_fire_intensity": 13816.143,
                "rate_of_spread": 10.418,
                "fire_type": "IC",
                "percentage_crown_fraction_burned": 0.887,
                "flame_length": 6.786,
                "sixty_minute_fire_size": 24.92,
                "thirty_minute_fire_size": 4.292,
                "critical_hours_hfi_4000": {
                    "start": 13.0,
                    "end": 22.0
                },
                "critical_hours_hfi_10000": {
                    "start": 15.0,
                    "end": 19.0
                }
            }
        ]
    }
