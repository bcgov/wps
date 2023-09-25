
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
async def test_c1_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "C1",
                "crown_base_height": 2,
                "percentage_conifer": 100
            }
        ]
    })

    assert response.status_code == 200

    assert response.json()['stations'][0]['id'] == 0
    assert response.json()['stations'][0]['station_code'] == 230
    assert response.json()['stations'][0]['station_name'] == 'HORSEFLY'
    assert response.json()['stations'][0]['zone_code'] == 'C3'
    assert response.json()['stations'][0]['elevation'] == 701
    assert response.json()['stations'][0]['fuel_type'] == 'C1'

    assert math.isclose(response.json()['stations'][0]['fine_fuel_moisture_code'], 90.683, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['drought_code'], 340.544, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['initial_spread_index'], 7.51, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['build_up_index'], 117.899, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['duff_moisture_code'], 103.923, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['fire_weather_index'], 27.913, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['head_fire_intensity'], 540.41, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['rate_of_spread'], 1.274, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['percentage_crown_fraction_burned'], 0.0, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['flame_length'], 1.342, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['sixty_minute_fire_size'], 0.253, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['thirty_minute_fire_size'], 0.045, abs_tol=0.001)

    assert response.json()['stations'][0]['fire_type'] == 'SUR'
    assert response.json()['stations'][0]['critical_hours_hfi_4000'] is None
    assert response.json()['stations'][0]['critical_hours_hfi_10000'] is None


@pytest.mark.anyio
@pytest.mark.usefixtures('mock_jwt_decode')
async def test_c1_no_daily_data_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 836,
                "fuel_type": "C1",
                "crown_base_height": 2
            }
        ]
    })

    assert response.status_code == 200
    assert response.json() == {
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 836,
                "station_name": "AUGUST LAKE",
                "zone_code": "K6",
                "elevation": 855,
                "fuel_type": "C1",
                "status": "N/A",
                "temp": None,
                "rh": None,
                "wind_direction": None,
                "wind_speed": None,
                "precipitation": None,
                "grass_cure": None,
                "fine_fuel_moisture_code": None,
                "drought_code": None,
                "initial_spread_index": None,
                "build_up_index": None,
                "duff_moisture_code": None,
                "fire_weather_index": None,
                "head_fire_intensity": None,
                "rate_of_spread": None,
                "fire_type": None,
                "percentage_crown_fraction_burned": None,
                "flame_length": None,
                "sixty_minute_fire_size": None,
                "thirty_minute_fire_size": None,
                "critical_hours_hfi_4000": None,
                "critical_hours_hfi_10000": None
            }
        ]
    }


@pytest.mark.anyio
@pytest.mark.usefixtures('mock_jwt_decode')
async def test_c1_forecast_request_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-06",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "C1",
                "crown_base_height": 2
            }
        ]
    })

    assert response.status_code == 200

    assert response.json()['stations'][0]['id'] == 0
    assert response.json()['stations'][0]['station_code'] == 230
    assert response.json()['stations'][0]['station_name'] == 'HORSEFLY'
    assert response.json()['stations'][0]['zone_code'] == 'C3'
    assert response.json()['stations'][0]['elevation'] == 701
    assert response.json()['stations'][0]['fuel_type'] == 'C1'

    assert math.isclose(response.json()['stations'][0]['fine_fuel_moisture_code'], 93.305, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['drought_code'], 340.544, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['initial_spread_index'], 10.88, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['build_up_index'], 117.899, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['duff_moisture_code'], 103.923, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['fire_weather_index'], 35.793, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['head_fire_intensity'], 2382.172, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['rate_of_spread'], 4.336, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['percentage_crown_fraction_burned'], 0.503, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['flame_length'], 2.818, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['sixty_minute_fire_size'], 2.973, abs_tol=0.001)
    assert math.isclose(response.json()['stations'][0]['thirty_minute_fire_size'], 0.531, abs_tol=0.001)

    assert response.json()['stations'][0]['fire_type'] == 'IC'
    assert response.json()['stations'][0]['critical_hours_hfi_4000'] is None
    assert response.json()['stations'][0]['critical_hours_hfi_10000'] is None


@pytest.mark.anyio
@pytest.mark.usefixtures('mock_jwt_decode')
async def test_c1_request_multiple_response(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    response = await async_client.post(firebat_url, json={
        "date": "2021-07-05",
        "stations": [
            {
                "id": 0,
                "station_code": 230,
                "fuel_type": "C1",
                "crown_base_height": 2
            },
            {
                "id": 1,
                "station_code": 230,
                "fuel_type": "C1",
                "crown_base_height": 2
            },
            {
                "id": 2,
                "station_code": 230,
                "fuel_type": "C1",
                "crown_base_height": 3
            }
        ]
    })

    assert response.status_code == 200

    for idx, station in enumerate(response.json()['stations']):
        assert station['id'] == idx
        assert station['station_code'] == 230
        assert station['station_name'] == 'HORSEFLY'
        assert station['zone_code'] == 'C3'
        assert station['elevation'] == 701
        assert station['fuel_type'] == 'C1'
        assert station['fine_fuel_moisture_code']

        assert math.isclose(station['fine_fuel_moisture_code'], 90.683, abs_tol=0.001)
        assert math.isclose(station['drought_code'], 340.544, abs_tol=0.001)
        assert math.isclose(station['initial_spread_index'], 7.51, abs_tol=0.001)
        assert math.isclose(station['build_up_index'], 117.899, abs_tol=0.001)
        assert math.isclose(station['duff_moisture_code'], 103.923, abs_tol=0.001)
        assert math.isclose(station['fire_weather_index'], 27.913, abs_tol=0.001)
        assert math.isclose(station['head_fire_intensity'], 540.409, abs_tol=0.001)
        assert math.isclose(station['rate_of_spread'], 1.274, abs_tol=0.001)
        assert math.isclose(station['percentage_crown_fraction_burned'], 0.0, abs_tol=0.001)
        assert math.isclose(station['flame_length'], 1.342, abs_tol=0.001)
        assert math.isclose(station['sixty_minute_fire_size'], 0.252, abs_tol=0.001)
        assert math.isclose(station['thirty_minute_fire_size'], 0.045, abs_tol=0.001)

        assert station['critical_hours_hfi_4000'] is None
        assert station['critical_hours_hfi_10000'] is None
