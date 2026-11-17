from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient
from wps_shared.tests.common import default_mock_client_get
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import DAILY, ByTimeTable
from wps_weather_data.wf1 import daily_actuals_table

import app.main
from app.routers.climatology import get_by_station_table

URL = "/api/climatology/stations/322/daily"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer token"}


def daily(year, temperature, station_code=322, precipitation=1.5):
    return SimpleNamespace(
        code=station_code,
        for_datetime=datetime(year, 7, 1, 20, tzinfo=UTC),
        temperature=temperature,
        relative_humidity=40.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=precipitation,
    )


@pytest.fixture
def by_station_table(tmp_path, monkeypatch):
    """A local by_station table with three years of 1 July for station 322, and one other
    station."""
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [daily(2024, 10.0), daily(2025, 20.0), daily(2026, 30.0), daily(2025, 99.0, 209)],
            datetime(2026, 7, 2, tzinfo=UTC),
        )
    )
    table = ByStationTable(str(tmp_path / "by_station"))
    for year in (2024, 2025, 2026):
        table.build_year(by_time, DAILY, year)
    monkeypatch.setitem(app.main.api.dependency_overrides, get_by_station_table, lambda: table)
    return table


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    return TestClient(app.main.app)


def test_daily_climatology_requires_authentication(client, by_station_table):
    assert client.get(URL).status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_compares_a_year_with_the_others(client, by_station_table):
    response = client.get(URL, params={"year": 2026}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "station_code": 322,
        "variable": "temperature",
        "year": 2026,
        "first_reference_year": 2024,
        "last_reference_year": 2025,
        "days": [
            {
                "month": 7,
                "day": 1,
                "count": 2,
                "minimum": 10.0,
                "p25": 12.5,
                "median": 15.0,
                "p75": 17.5,
                "p90": 19.0,
                "maximum": 20.0,
            }
        ],
        "observations": [{"date": "2026-07-01", "value": 30.0}],
    }


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_takes_a_variable(client, by_station_table):
    response = client.get(URL, params={"year": 2026, "variable": "precipitation"}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["variable"] == "precipitation"
    assert response.json()["days"][0]["median"] == 1.5


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_defaults_to_the_current_year(client, by_station_table, mocker):
    mocker.patch(
        "app.routers.climatology.get_utc_now", return_value=datetime(2025, 8, 1, tzinfo=UTC)
    )

    response = client.get(URL, headers=HEADERS)

    assert response.json()["year"] == 2025
    assert response.json()["observations"] == [{"date": "2025-07-01", "value": 20.0}]


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_rejects_an_unknown_variable(client, by_station_table):
    response = client.get(URL, params={"variable": "dew_point"}, headers=HEADERS)

    assert response.status_code == 422


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_of_a_station_with_no_data_is_empty(client, by_station_table):
    response = client.get("/api/climatology/stations/1/daily", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["days"] == []


def test_get_by_station_table_returns_the_table_from_the_app_state():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(by_station_table=object())))

    assert get_by_station_table(request) is request.app.state.by_station_table
