from starlette.testclient import TestClient
import pytest
from app.schemas.observations import WeatherStationHourlyReadings
from app.schemas.stations import WeatherStation
from app.wildfire_one import wfwx_api


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures("mock_jwt_decode")
def test_multiple_stations(client: TestClient, monkeypatch):
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    codes = [1, 2]

    async def mock_get_auth_header(_):
        return dict()

    async def mock_hourly_readings(*_, **__):
        return [
            WeatherStationHourlyReadings(values=[],
                                         station=WeatherStation(code=codes[0],
                                                                name='one',
                                                                lat=1.0,
                                                                long=1.0)),
            WeatherStationHourlyReadings(values=[],
                                         station=WeatherStation(code=codes[1],
                                                                name='two',
                                                                lat=2.0,
                                                                long=2.0))]

    monkeypatch.setattr(wfwx_api, 'get_auth_header', mock_get_auth_header)
    monkeypatch.setattr('app.hourlies.get_hourly_readings', mock_hourly_readings)

    response = client.post('/api/observations/', json={"stations": codes})
    assert len(response.json()['hourlies']) == 2


@pytest.mark.usefixtures("mock_jwt_decode")
def test_single_station_single_value(client: TestClient, monkeypatch):
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    codes = [1]

    async def mock_get_auth_header(_):
        return dict()

    async def mock_hourly_readings(*_, **__):
        return [
            WeatherStationHourlyReadings(values=[],
                                         station=WeatherStation(code=codes[0],
                                                                name='one',
                                                                lat=1.0,
                                                                long=1.0))]

    monkeypatch.setattr(wfwx_api, 'get_auth_header', mock_get_auth_header)
    monkeypatch.setattr('app.hourlies.get_hourly_readings', mock_hourly_readings)

    response = client.post('/api/observations/', json={"stations": codes})
    assert len(response.json()['hourlies']) == 1
