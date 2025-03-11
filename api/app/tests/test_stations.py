from aiohttp import ClientSession
import pytest
import app.main
from datetime import datetime, timezone
from app.tests import load_json_file
from wps_shared.tests.common import default_mock_client_get
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "url, status, code, name, lat, long",
    [
        ("/api/stations/", 200, 331, "ASHNOLA", 49.13905, -120.1844),
        ("/api/stations/", 200, 322, "AFTON", 50.6733333, -120.4816667),
        ("/api/stations/", 200, 317, "ALLISON PASS", 49.0623139, -120.7674194),
    ],
)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_stations(
    client: TestClient,
    monkeypatch,
    url,
    status,
    code,
    name,
    lat,
    long,
):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response: Response = client.get(url)
    assert response.status_code == status
    station = next(x for x in response.json()["features"] if x["properties"]["code"] == code)
    assert station["properties"]["code"] == code, "Code"
    assert station["properties"]["name"] == name, "Name"
    assert station["geometry"]["coordinates"][1] == lat, "Latitude"
    assert station["geometry"]["coordinates"][0] == long, "Longitude"
    assert len(response.json()["features"]) >= 200


@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_station_details(client: TestClient, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    def mock_get_utc_now():
        return datetime.fromtimestamp(1618870929583 / 1000, tz=timezone.utc)

    monkeypatch.setattr(app.routers.stations, "get_utc_now", mock_get_utc_now)
    expected_response = load_json_file(__file__)("test_stations_details_expected_response.json")

    response: Response = client.get("/api/stations/details/")
    assert response.status_code == 200
    assert response.json() == expected_response
