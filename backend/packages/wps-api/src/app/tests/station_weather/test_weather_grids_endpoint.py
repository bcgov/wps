from datetime import UTC, datetime, timedelta

import icechunk
import numpy as np
import pytest
from starlette.testclient import TestClient
from wps_weather_data.grids.store import GridStore
from wps_weather_data.tests.grid_helpers import small_crop, variable_run

import app.weather_main
from app.routers.weather_grids import get_grid_stores

BASE = "/api/weather/v1/grids"
POINT = f"{BASE}/HRDPS/point"
KAMLOOPS = {"latitude": 50.9, "longitude": -120.44}
NEWEST = datetime(2026, 11, 23, 18, tzinfo=UTC)
# One that only `history` still holds.
OLD = NEWEST - timedelta(days=3)


def write_run(store: GridStore, run_time: datetime, celsius: float):
    values = {
        "temperature": celsius + 273.15,
        "relative_humidity": 40.0,
        "wind_speed": 10.0,
        "wind_direction": 270.0,
        "precipitation": 0.0,
    }
    hours = len(store.model.forecast_hours(run_time))
    store.write_run(
        run_time,
        small_crop(),
        [variable_run(v, np.full(hours, values[v.name])) for v in store.model.variables],
    )


@pytest.fixture
def stores(tmp_path, monkeypatch):
    """HRDPS has runs in both stores, and GDPS has no stores yet."""

    def model_stores(model):
        return tuple(
            GridStore(model, kind, icechunk.local_filesystem_storage(str(tmp_path / model / kind)))
            for kind in ("recent", "history")
        )

    stores = {model: model_stores(model) for model in ("HRDPS", "GDPS")}
    recent, history = stores["HRDPS"]
    write_run(recent, NEWEST - timedelta(hours=6), 5.0)
    write_run(recent, NEWEST, 10.0)
    write_run(history, NEWEST, 10.0)
    write_run(history, OLD, -3.0)
    overrides = app.weather_main.api.dependency_overrides
    monkeypatch.setitem(overrides, get_grid_stores, lambda: stores)
    return stores


@pytest.fixture
def client():
    return TestClient(app.weather_main.app)


@pytest.mark.usefixtures("stores")
def test_runs_are_listed_once_newest_first(client):
    response = client.get(f"{BASE}/HRDPS/runs")

    assert response.json() == {
        "model": "HRDPS",
        "runs": [
            {"run_timestamp": "2026-11-23T18:00:00Z", "last_forecast_hour": 48},
            {"run_timestamp": "2026-11-23T12:00:00Z", "last_forecast_hour": 48},
            {"run_timestamp": "2026-11-20T18:00:00Z", "last_forecast_hour": 48},
        ],
    }


def test_a_model_with_no_grids_yet_has_no_runs(client, stores):
    assert client.get(f"{BASE}/GDPS/runs").json()["runs"] == []
    response = client.get(f"{BASE}/GDPS/point", params=KAMLOOPS)
    assert response.status_code == 404
    assert response.json() == {"detail": "No GDPS runs kept"}
    assert not any(store.exists() for store in stores["GDPS"])


@pytest.mark.usefixtures("stores")
def test_the_newest_runs_forecast_at_the_nearest_cell(client):
    response = client.get(POINT, params=KAMLOOPS)

    assert response.status_code == 200
    body = response.json()
    assert (body["model"], body["latitude"], body["longitude"]) == ("HRDPS", 51.0, -120.5)
    assert len(body["rows"]) == 49
    assert body["rows"][1] == {
        "timestamp": "2026-11-23T19:00:00Z",
        "run_timestamp": "2026-11-23T18:00:00Z",
        "forecast_hour": 1,
        "temperature": 10.0,
        "relative_humidity": 40.0,
        "wind_speed": 36.0,
        "wind_direction": 270.0,
        "precipitation": 0.0,
    }


@pytest.mark.usefixtures("stores")
@pytest.mark.parametrize(
    "run_timestamp, temperature",
    [
        ("2026-11-23T12:00:00Z", 5.0),
        ("2026-11-23T12:00:00", 5.0),
        ("2026-11-23T04:00:00-08:00", 5.0),
        ("2026-11-20T18:00:00Z", -3.0),
    ],
)
def test_a_run_can_be_asked_for(client, run_timestamp, temperature):
    """From either store. A time with no offset is UTC."""
    response = client.get(POINT, params={**KAMLOOPS, "run_timestamp": run_timestamp})

    assert response.json()["rows"][0]["temperature"] == temperature


@pytest.mark.usefixtures("stores")
def test_a_run_that_is_not_kept_is_not_found(client):
    response = client.get(POINT, params={**KAMLOOPS, "run_timestamp": "2026-11-01T00:00:00Z"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No HRDPS run 2026-11-01T00:00:00+00:00 kept"}


@pytest.mark.usefixtures("stores")
@pytest.mark.parametrize(
    "url, params, location",
    [
        (POINT, {"latitude": 45, "longitude": -120}, ["query", "latitude"]),
        (POINT, {"latitude": 50, "longitude": 120}, ["query", "longitude"]),
        (POINT, {"latitude": 50}, ["query", "longitude"]),
        (POINT, {**KAMLOOPS, "run_timestamp": "yesterday"}, ["query", "run_timestamp"]),
        (f"{BASE}/NAM/point", KAMLOOPS, ["path", "model"]),
    ],
)
def test_invalid_parameters_are_refused(client, url, params, location):
    response = client.get(url, params=params)

    assert response.status_code == 422
    assert [error["loc"] for error in response.json()["detail"]] == [location]


@pytest.mark.usefixtures("stores")
def test_csv_when_asked_for(client):
    headers = {"Accept": "text/csv"}

    point = client.get(POINT, params=KAMLOOPS, headers=headers)
    runs = client.get(f"{BASE}/HRDPS/runs", headers=headers)

    assert point.headers["content-type"].startswith("text/csv")
    assert point.text.splitlines()[:2] == [
        '"timestamp","run_timestamp","forecast_hour","temperature","relative_humidity",'
        '"wind_speed","wind_direction","precipitation"',
        '"2026-11-23T18:00:00Z","2026-11-23T18:00:00Z",0,10,40,36,270,0',
    ]
    assert runs.text.splitlines()[:2] == [
        '"run_timestamp","last_forecast_hour"',
        '"2026-11-23T18:00:00Z",48',
    ]


def test_a_new_run_is_seen_without_a_restart(client, stores):
    client.get(POINT, params=KAMLOOPS)

    recent, _ = stores["HRDPS"]
    write_run(recent, NEWEST + timedelta(hours=6), 12.0)

    assert client.get(POINT, params=KAMLOOPS).json()["rows"][0]["temperature"] == 12.0


def test_every_model_with_grids_has_stores():
    """The stores are opened when first read, so starting up does not contact the object store."""
    with TestClient(app.weather_main.app):
        assert list(app.weather_main.api.state.grid_stores) == [
            "HRDPS",
            "RDPS",
            "GDPS",
            "GFS",
            "ECMWF",
        ]
