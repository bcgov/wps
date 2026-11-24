from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import DAILY, ByTimeTable
from wps_weather_data.stations import StationsTable, stations_table
from wps_weather_data.wf1 import daily_actuals_table, forecasts_table

import app.weather_main
from app.routers import station_weather
from app.routers.station_weather import (
    get_by_station_table,
    get_by_time_table,
    get_stations_table,
)

BASE = "/api/weather/v1"
URL = f"{BASE}/observations/daily"
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


def forecast(time, temperature):
    return SimpleNamespace(
        station_code=322,
        weather_date=time,
        temperature=temperature,
        relative_humidity=30.0,
        wind_speed=10.0,
        wind_direction=270.0,
        precipitation=0.0,
        ffmc=90.0,
        created_at=FETCHED,
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
    by_time.merge_wf1_rows(forecasts_table([forecast(noon(7, 1), 22.0)], FETCHED))
    for year in (2025, 2026):
        by_station.build_year(by_time, DAILY, year)
    # Since the nightly build: a correction to 18 July and a new day.
    by_time.merge_wf1_rows(
        daily_actuals_table([daily(noon(7, 18), 26.0), daily(noon(7, 19), 27.0)], NOW)
    )
    stations = StationsTable(str(tmp_path / "stations"))
    stations.replace(
        stations_table(
            [
                {
                    "stationCode": 322,
                    "displayLabel": "AFTON",
                    "latitude": 50.67,
                    "longitude": -120.48,
                    "elevation": 780,
                    "stationStatus": {"id": "ACTIVE"},
                },
                {"stationCode": 209, "displayLabel": "ALEXIS CREEK", "latitude": 52.08},
            ],
            FETCHED,
        )
    )

    overrides = app.weather_main.api.dependency_overrides
    monkeypatch.setitem(overrides, get_by_station_table, lambda: by_station)
    monkeypatch.setitem(overrides, get_by_time_table, lambda: by_time)
    monkeypatch.setitem(overrides, get_stations_table, lambda: stations)
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
    assert (body["resolution"], body["start"], body["end"]) == (
        "daily",
        "2026-07-01",
        "2026-07-01",
    )
    [row] = body["rows"]
    assert row["timestamp"] == "2026-07-01T20:00:00Z"
    # Stored as float32, returned as written.
    assert row["temperature"] == 21.3
    # Only an observation's fields.
    assert "ffmc" in row
    for field in ("source", "run_timestamp", "bias_adjusted_temperature"):
        assert field not in row


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
def test_observations_default_to_the_last_week(client):
    response = client.get(URL, params={"station_codes": 322})

    body = response.json()
    assert (body["start"], body["end"]) == ("2026-07-14", "2026-07-20")
    assert values(response, "timestamp") == [("2026-07-18T20:00:00Z",), ("2026-07-19T20:00:00Z",)]


@pytest.mark.parametrize(
    "station_codes", ["322,209", ["322", "209"], ["322,209", "322"], " 322 , 209"]
)
@pytest.mark.usefixtures("tables")
def test_station_codes_comma_separated_or_repeated(client, station_codes):
    response = client.get(
        URL, params={"station_codes": station_codes, "start": "2026-07-01", "end": "2026-07-01"}
    )

    assert response.json()["station_codes"] == [322, 209]
    assert values(response, "station_code", "temperature") == [(209, 9.0), (322, 21.3)]


@pytest.mark.parametrize("station_codes", ["afton", ",", ",".join(str(n) for n in range(51))])
@pytest.mark.usefixtures("tables")
def test_bad_station_codes_are_rejected(client, station_codes):
    response = client.get(URL, params={"station_codes": station_codes})
    assert response.status_code == 422


@pytest.mark.usefixtures("tables")
def test_forecasts_have_only_forecast_fields(client):
    response = client.get(
        f"{BASE}/forecasts/daily",
        params={"station_codes": 322, "start": "2026-07-01", "end": "2026-07-01"},
    )

    body = response.json()
    assert "resolution" not in body
    [row] = body["rows"]
    assert (row["temperature"], row["ffmc"]) == (22.0, 90.0)
    for field in ("danger_rating", "observation_valid", "run_timestamp"):
        assert field not in row


@pytest.mark.usefixtures("tables")
def test_forecasts_default_to_the_next_ten_days(client):
    body = client.get(f"{BASE}/forecasts/daily", params={"station_codes": 322}).json()
    assert (body["start"], body["end"]) == ("2026-07-20", "2026-07-29")


@pytest.mark.usefixtures("tables")
def test_model_values(client):
    response = client.get(
        f"{BASE}/models/GDPS/daily",
        params={"station_codes": "322,209", "start": "2026-07-01", "end": "2026-07-01"},
    )

    body = response.json()
    assert (body["model"], body["resolution"]) == ("GDPS", "daily")
    [row] = body["rows"]
    assert (row["station_code"], row["temperature"]) == (322, 19.0)
    assert row["run_timestamp"] == "2026-07-01T12:00:00Z"
    assert "ffmc" not in row


@pytest.mark.usefixtures("tables")
def test_unknown_model_is_rejected(client):
    response = client.get(f"{BASE}/models/gdps/daily", params={"station_codes": 322})
    assert response.status_code == 422


@pytest.mark.usefixtures("tables")
def test_stations(client):
    response = client.get(f"{BASE}/stations")

    assert response.json()["stations"] == [
        {
            "station_code": 209,
            "name": "ALEXIS CREEK",
            "latitude": 52.08,
            "longitude": None,
            "elevation": None,
            "status": None,
        },
        {
            "station_code": 322,
            "name": "AFTON",
            "latitude": 50.67,
            "longitude": -120.48,
            "elevation": 780.0,
            "status": "ACTIVE",
        },
    ]


def test_no_stations_yet(client, tmp_path, monkeypatch):
    stations = StationsTable(str(tmp_path / "stations"))
    monkeypatch.setitem(
        app.weather_main.api.dependency_overrides, get_stations_table, lambda: stations
    )
    assert client.get(f"{BASE}/stations").json() == {"stations": []}


@pytest.mark.usefixtures("tables")
def test_csv_when_asked_for(client):
    response = client.get(
        URL,
        params={"station_codes": "322,209", "start": "2026-07-01", "end": "2026-07-01"},
        headers={"Accept": "text/csv"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    header, first, second = response.text.splitlines()
    assert header.startswith('"station_code","timestamp","temperature","relative_humidity"')
    assert first.startswith('209,"2026-07-01T20:00:00Z",9,40,')
    assert second.startswith('322,"2026-07-01T20:00:00Z",21.3,40,')


@pytest.mark.usefixtures("tables")
def test_stations_as_csv(client):
    response = client.get(f"{BASE}/stations", headers={"Accept": "text/csv"})
    assert response.text.splitlines()[2] == '322,"AFTON",50.67,-120.48,780,"ACTIVE"'


@pytest.mark.usefixtures("tables")
def test_end_before_start_is_rejected(client):
    response = client.get(
        URL, params={"station_codes": 322, "start": "2026-07-02", "end": "2026-07-01"}
    )
    assert response.status_code == 422


@pytest.mark.usefixtures("tables")
def test_a_long_request_comes_back_in_pages(client, monkeypatch):
    monkeypatch.setattr(station_weather, "PAGE_ROWS", 2)
    params = {"station_codes": 322, "start": "2026-07-17", "end": "2026-07-20"}

    first = client.get(URL, params=params)

    body = first.json()
    assert (body["start"], body["end"]) == ("2026-07-17", "2026-07-18")
    assert values(first, "timestamp") == [("2026-07-18T20:00:00Z",)]
    next_url = (
        "/api/weather/v1/observations/daily?station_codes=322&start=2026-07-19&end=2026-07-20"
    )
    assert body["next"] == next_url
    assert first.headers["link"] == f'<{next_url}>; rel="next"'

    last = client.get(next_url)

    body = last.json()
    assert (body["start"], body["end"]) == ("2026-07-19", "2026-07-20")
    assert values(last, "timestamp") == [("2026-07-19T20:00:00Z",)]
    assert body["next"] is None
    assert "link" not in last.headers


@pytest.mark.usefixtures("tables")
def test_a_page_has_every_station_for_at_least_a_day(client, monkeypatch):
    monkeypatch.setattr(station_weather, "PAGE_ROWS", 1)

    response = client.get(
        URL, params={"station_codes": "322,209", "start": "2026-07-01", "end": "2026-07-02"}
    )

    assert values(response, "station_code") == [(209,), (322,)]
    assert response.json()["next"].endswith("start=2026-07-02&end=2026-07-02")


@pytest.mark.usefixtures("tables")
def test_the_next_page_keeps_a_defaulted_end(client, monkeypatch):
    monkeypatch.setattr(station_weather, "PAGE_ROWS", 3)

    body = client.get(URL, params={"station_codes": 322, "start": "2026-07-14"}).json()

    assert (body["start"], body["end"]) == ("2026-07-14", "2026-07-16")
    assert body["next"].endswith("start=2026-07-17&end=2026-07-20")


@pytest.mark.usefixtures("tables")
def test_csv_pages_link_in_the_header(client, monkeypatch):
    monkeypatch.setattr(station_weather, "PAGE_ROWS", 1)

    response = client.get(
        URL,
        params={"station_codes": 322, "start": "2026-07-18", "end": "2026-07-19"},
        headers={"Accept": "text/csv"},
    )

    assert len(response.text.splitlines()) == 2
    assert "start=2026-07-19" in response.headers["link"]


@pytest.mark.usefixtures("tables")
def test_hourly_years_are_paged_not_rejected(client):
    response = client.get(
        f"{BASE}/observations/hourly",
        params={"station_codes": 322, "start": "2020-01-01", "end": "2025-12-31"},
    )

    assert response.status_code == 200
    body = response.json()
    # 50,000 rows is 2,083 days of 24 hours.
    assert (body["start"], body["end"]) == ("2020-01-01", "2025-09-13")
    assert body["next"].endswith("start=2025-09-14&end=2025-12-31")


def test_docs_are_served_under_weather(client):
    assert client.get("/api/weather/docs").status_code == 200
    paths = client.get("/api/weather/openapi.json").json()["paths"]
    assert list(paths) == [
        "/weather/v1/stations",
        "/weather/v1/observations/{resolution}",
        "/weather/v1/forecasts/daily",
        "/weather/v1/models/{model}/{resolution}",
        "/weather/v1/grids/{model}/runs",
        "/weather/v1/grids/{model}/point",
    ]


@pytest.mark.parametrize(
    ("params", "parameter"),
    [
        ({"station_codes": "afton"}, "station_codes"),
        ({"station_codes": 322, "start": "2026-07-02", "end": "2026-07-01"}, "end"),
        # Checked by FastAPI itself.
        ({"station_codes": 322, "start": "July"}, "start"),
    ],
)
@pytest.mark.usefixtures("tables")
def test_every_422_has_fastapis_shape(client, params, parameter):
    response = client.get(URL, params=params)

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert error["loc"] == ["query", parameter]
    assert error["msg"]
