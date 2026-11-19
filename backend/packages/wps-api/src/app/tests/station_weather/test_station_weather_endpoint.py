from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import DAILY, ByTimeTable
from wps_weather_data.wf1 import daily_actuals_table

import app.weather_main
from app.routers import station_weather
from app.routers.station_weather import get_by_station_table, get_by_time_table

URL = "/api/weather/v1/daily"
NOW = datetime(2026, 7, 20, 12, tzinfo=UTC)
FETCHED = datetime(2026, 7, 1, tzinfo=UTC)


def noon(month, day, year=2026):
    return datetime(year, month, day, 20, tzinfo=UTC)


def daily(time, temperature, station_code=322):
    return SimpleNamespace(
        code=station_code,
        for_datetime=time,
        temperature=temperature,
        relative_humidity=40.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=1.5,
    )


def model_row(time, temperature):
    return {
        "station_code": 322,
        "prediction_timestamp": time,
        "tmp_tgl_2": temperature,
        "rh_tgl_2": 50.0,
        "wind_tgl_10": 5.0,
        "wdir_tgl_10": 180.0,
        "precip_24h": 4.0,
    }


@pytest.fixture
def tables(tmp_path, monkeypatch):
    """by_station built on the night of 18 July; by_time has had a day of data since."""
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    by_station = ByStationTable(str(tmp_path / "by_station"))
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [
                daily(noon(7, 1, 2025), 15.0),
                daily(noon(7, 1), 21.3),
                daily(noon(7, 1), 9.0, station_code=209),
                daily(noon(7, 18), 25.0),
            ],
            FETCHED,
        )
    )
    by_time.merge_run(
        ModelEnum.GDPS, noon(7, 1) - timedelta(hours=8), [model_row(noon(7, 1), 19.0)]
    )
    for year in (2025, 2026):
        by_station.build_year(by_time, DAILY, year)
    # Since the nightly build: a correction to 18 July and a new day.
    by_time.merge_wf1_rows(
        daily_actuals_table([daily(noon(7, 18), 26.0), daily(noon(7, 19), 27.0)], NOW)
    )

    overrides = app.weather_main.api.dependency_overrides
    monkeypatch.setitem(overrides, get_by_station_table, lambda: by_station)
    monkeypatch.setitem(overrides, get_by_time_table, lambda: by_time)
    monkeypatch.setattr(station_weather, "get_utc_now", lambda: NOW)


@pytest.fixture
def client():
    return TestClient(app.weather_main.app)


def values(response, *keys):
    return [tuple(row[key] for key in keys) for row in response.json()["rows"]]


@pytest.mark.usefixtures("tables")
def test_reads_history_for_the_dates_asked_for(client):
    response = client.get(
        URL, params={"station_codes": 322, "start": "2026-07-01", "end": "2026-07-01"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == ["ACTUALS"]
    [row] = body["rows"]
    assert row["timestamp"] == "2026-07-01T20:00:00Z"
    assert row["source"] == "ACTUALS"
    # Stored as float32, returned as written.
    assert row["temperature"] == 21.3
    assert row["run_timestamp"] is None


@pytest.mark.usefixtures("tables")
def test_spans_years(client):
    response = client.get(
        URL, params={"station_codes": 322, "start": "2025-06-01", "end": "2026-07-01"}
    )

    assert values(response, "timestamp", "temperature") == [
        ("2025-07-01T20:00:00Z", 15.0),
        ("2026-07-01T20:00:00Z", 21.3),
    ]


@pytest.mark.usefixtures("tables")
def test_recent_days_come_from_by_time(client):
    response = client.get(
        URL, params={"station_codes": 322, "start": "2026-07-17", "end": "2026-07-25"}
    )

    assert values(response, "timestamp", "temperature") == [
        ("2026-07-18T20:00:00Z", 26.0),
        ("2026-07-19T20:00:00Z", 27.0),
    ]


@pytest.mark.usefixtures("tables")
def test_sorted_by_station_then_source(client):
    response = client.get(
        URL,
        params={
            "station_codes": [322, 209],
            "sources": ["GDPS", "ACTUALS"],
            "start": "2026-07-01",
            "end": "2026-07-01",
        },
    )

    assert values(response, "station_code", "source", "temperature") == [
        (209, "ACTUALS", 9.0),
        (322, "ACTUALS", 21.3),
        (322, "GDPS", 19.0),
    ]
    assert response.json()["rows"][2]["run_timestamp"] == "2026-07-01T12:00:00Z"


@pytest.mark.usefixtures("tables")
def test_end_before_start_is_rejected(client):
    response = client.get(
        URL, params={"station_codes": 322, "start": "2026-07-02", "end": "2026-07-01"}
    )
    assert response.status_code == 422


@pytest.mark.usefixtures("tables")
def test_too_many_rows_is_rejected(client):
    # 3 years of hourly for one station and source is over 26,000 rows; two sources is over the
    # limit.
    response = client.get(
        "/api/weather/v1/hourly",
        params={
            "station_codes": 322,
            "sources": ["ACTUALS", "GDPS"],
            "start": "2024-01-01",
            "end": "2026-12-31",
        },
    )
    assert response.status_code == 422
    assert "limit is 50000" in response.json()["detail"]


@pytest.mark.usefixtures("tables")
def test_unknown_source_is_rejected(client):
    response = client.get(
        URL,
        params={
            "station_codes": 322,
            "sources": "actuals",
            "start": "2026-07-01",
            "end": "2026-07-01",
        },
    )
    assert response.status_code == 422


def test_docs_are_served_under_weather(client):
    assert client.get("/api/weather/docs").status_code == 200
    paths = client.get("/api/weather/openapi.json").json()["paths"]
    assert list(paths) == ["/weather/v1/{resolution}"]
