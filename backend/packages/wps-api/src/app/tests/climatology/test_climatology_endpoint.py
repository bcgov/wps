from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient
from wps_shared.schemas.fba import FireCenterStation, WFWXFireCentre
from wps_shared.tests.common import default_mock_client_get
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import DAILY, ByTimeTable
from wps_weather_data.wf1 import daily_actuals_table

import app.main
from app.routers.climatology import MAX_COMPARE_YEARS, MAX_STATIONS, get_by_station_table

URL = "/api/climatology/daily"
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
    """A local by_station table with three years of 1 July for stations 322 and 209."""
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [
                daily(2024, 10.0),
                daily(2025, 20.0),
                daily(2026, 30.0),
                daily(2024, 0.0, 209),
                daily(2025, 4.0, 209),
                daily(2026, 6.0, 209),
            ],
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
    assert client.get(URL, params={"station_codes": 322}).status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_of_one_station(client, by_station_table):
    response = client.get(URL, params={"station_codes": 322, "year": 2026}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "variable": "temperature",
        "year": 2026,
        "method": "average",
        "series": [
            {
                "station_codes": [322],
                "first_reference_year": 2024,
                "last_reference_year": 2025,
                "days": [
                    {
                        "month": 7,
                        "day": 1,
                        "count": 2,
                        "station_count": 1,
                        "minimum": 10.0,
                        "p25": 12.5,
                        "median": 15.0,
                        "p75": 17.5,
                        "p90": 19.0,
                        "maximum": 20.0,
                    }
                ],
                "observations": [{"date": "2026-07-01", "value": 30.0, "station_count": 1}],
                "compared_years": [],
            }
        ],
    }


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize(
    "method, series_count, minimum",
    [("average", 1, 5.0), ("pooled", 1, 0.0), ("each", 2, 10.0)],
)
def test_daily_climatology_of_several_stations(
    client, by_station_table, method, series_count, minimum
):
    response = client.get(
        URL,
        params={"station_codes": [322, 209], "year": 2026, "method": method},
        headers=HEADERS,
    )

    assert response.status_code == 200
    series = response.json()["series"]
    assert len(series) == series_count
    assert series[0]["days"][0]["minimum"] == minimum


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_compares_years(client, by_station_table):
    response = client.get(
        URL,
        params={"station_codes": 322, "year": 2026, "compare_years": [2025, 2024]},
        headers=HEADERS,
    )

    (series,) = response.json()["series"]
    assert series["compared_years"] == [
        {
            "year": 2025,
            "observations": [{"date": "2025-07-01", "value": 20.0, "station_count": 1}],
        },
        {
            "year": 2024,
            "observations": [{"date": "2024-07-01", "value": 10.0, "station_count": 1}],
        },
    ]
    # They are still part of what the year is compared with.
    assert series["days"][0]["count"] == 2


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_takes_a_variable(client, by_station_table):
    response = client.get(
        URL,
        params={"station_codes": 322, "year": 2026, "variable": "precipitation"},
        headers=HEADERS,
    )

    assert response.json()["variable"] == "precipitation"
    assert response.json()["series"][0]["days"][0]["median"] == 1.5


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_defaults_to_the_current_year(client, by_station_table, mocker):
    mocker.patch(
        "app.routers.climatology.get_utc_now", return_value=datetime(2025, 8, 1, tzinfo=UTC)
    )

    response = client.get(URL, params={"station_codes": 322}, headers=HEADERS)

    assert response.json()["year"] == 2025
    assert response.json()["series"][0]["observations"] == [
        {"date": "2025-07-01", "value": 20.0, "station_count": 1}
    ]


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize(
    "params",
    [
        {},
        {"station_codes": 322, "variable": "dew_point"},
        {"station_codes": 322, "method": "median"},
        {"station_codes": list(range(MAX_STATIONS + 1))},
        {"station_codes": 322, "compare_years": list(range(2000, 2001 + MAX_COMPARE_YEARS))},
        {"station_codes": 322, "compare_years": "last"},
    ],
)
def test_daily_climatology_rejects_a_bad_request(client, by_station_table, params):
    assert client.get(URL, params=params, headers=HEADERS).status_code == 422


@pytest.mark.usefixtures("mock_jwt_decode")
def test_daily_climatology_of_a_station_with_no_data_is_empty(client, by_station_table):
    response = client.get(URL, params={"station_codes": 1}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["series"][0]["days"] == []


@pytest.mark.usefixtures("mock_jwt_decode")
def test_fire_centres_list_their_stations_and_zones_in_name_order(client, mocker):
    centres = [
        WFWXFireCentre(
            id=2,
            name="Kamloops Fire Centre",
            stations=[
                FireCenterStation(code=322, name="SPARKS", zone="K2"),
                FireCenterStation(code=209, name="ALEXIS CREEK", zone="K4"),
            ],
        ),
        WFWXFireCentre(id=1, name="Cariboo Fire Centre", stations=None),
    ]
    mocker.patch("app.routers.climatology.WfwxApi.get_fire_centers", return_value=centres)

    response = client.get("/api/climatology/fire-centres", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "fire_centres": [
            {"id": 1, "name": "Cariboo Fire Centre", "stations": []},
            {
                "id": 2,
                "name": "Kamloops Fire Centre",
                "stations": [
                    {"code": 209, "name": "ALEXIS CREEK", "zone": "K4"},
                    {"code": 322, "name": "SPARKS", "zone": "K2"},
                ],
            },
        ]
    }


def test_get_by_station_table_returns_the_table_from_the_app_state():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(by_station_table=object())))

    assert get_by_station_table(request) is request.app.state.by_station_table
