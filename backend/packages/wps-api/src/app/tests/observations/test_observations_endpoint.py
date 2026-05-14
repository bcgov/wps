from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from wps_shared.schemas.observations import WeatherStationHourlyReadings
from wps_shared.schemas.stations import WeatherStation


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures("mock_jwt_decode")
def test_multiple_stations(client: TestClient, mocker, mock_wfwx_api):
    """Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    codes = [1, 2]

    mock_hourly_readings = [
        WeatherStationHourlyReadings(
            values=[], station=WeatherStation(code=codes[0], name="one", lat=1.0, long=1.0)
        ),
        WeatherStationHourlyReadings(
            values=[], station=WeatherStation(code=codes[1], name="two", lat=2.0, long=2.0)
        ),
    ]

    mock_wfwx_api.get_hourly_readings = AsyncMock(return_value=mock_hourly_readings)
    mocker.patch("app.hourlies.WfwxApi", return_value=mock_wfwx_api)

    response = client.post("/api/observations/", json={"stations": codes})
    assert len(response.json()["hourlies"]) == 2


@pytest.mark.usefixtures("mock_jwt_decode")
def test_single_station_single_value(client: TestClient, mocker, mock_wfwx_api):
    """Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    codes = [1]

    mock_hourly_readings = [
        WeatherStationHourlyReadings(
            values=[], station=WeatherStation(code=codes[0], name="one", lat=1.0, long=1.0)
        )
    ]

    mock_wfwx_api.get_hourly_readings = AsyncMock(return_value=mock_hourly_readings)
    mocker.patch("app.hourlies.WfwxApi", return_value=mock_wfwx_api)

    response = client.post("/api/observations/", json={"stations": codes})
    assert len(response.json()["hourlies"]) == 1
