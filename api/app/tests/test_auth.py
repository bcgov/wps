from fastapi.testclient import TestClient
from datetime import datetime, timezone
import pytest
import wps_shared.auth
import app.main
from app.tests import load_json_file


@pytest.mark.parametrize(
    "token, status, endpoint, verb, payload",
    [
        ("Basic token", 401, "/api/weather_models/GDPS/predictions/summaries/", "post", "test_auth_stations_payload.json"),
        ("just_token", 401, "/api/weather_models/GDPS/predictions/summaries/", "post", "test_auth_stations_payload.json"),
        ("Bearer token", 401, "/api/weather_models/GDPS/predictions/summaries/", "post", "test_auth_stations_payload.json"),
        ("just_token", 401, "/api/weather_models/GDPS/predictions/most_recent/", "post", "test_auth_stations_payload.json"),
        ("Bearer token", 401, "/api/weather_models/GDPS/predictions/most_recent/", "post", "test_auth_stations_payload.json"),
        ("just_token", 401, "/api/stations/details/", "get", "test_auth_stations_payload.json"),
    ],
)
@pytest.mark.usefixtures("mock_client_session")
def test_unauthenticated_requests(token, status, endpoint, verb, payload, spy_access_logging):
    client = TestClient(app.main.app)
    payload = load_json_file(__file__)(payload)
    response = None
    if verb == "post":
        response = client.post(endpoint, headers={"Authorization": token}, json=payload)
    else:
        response = client.get(endpoint, headers={"Authorization": token})

    assert response.status_code == status
    spy_access_logging.assert_called_once_with(None, False, endpoint)


@pytest.mark.parametrize(
    "status, endpoint, verb, utc_time",
    [
        (200, "/api/weather_models/GDPS/predictions/summaries/", "post", 1618870929583),
        (200, "/api/weather_models/GDPS/predictions/most_recent/", "post", 1618870929583),
        (200, "/api/stations/details/", "get", 1618870929583),
    ],
)
@pytest.mark.usefixtures("mock_client_session")
@pytest.mark.usefixtures("mock_jwt_decode")
def test_authenticated_requests(status, endpoint, verb, utc_time, spy_access_logging, monkeypatch):
    def mock_get_utc_now():
        return datetime.fromtimestamp(utc_time / 1000, tz=timezone.utc)

    monkeypatch.setattr(app.routers.stations, "get_utc_now", mock_get_utc_now)
    client = TestClient(app.main.app)
    response = None
    if verb == "post":
        response = client.post(endpoint, headers={"Authorization": "Bearer token"}, json={"stations": [838]})
    if verb == "get":
        response = client.get(endpoint, headers={"Authorization": "Bearer token"})

    assert response.status_code == status
    spy_access_logging.assert_called_once_with("test_username", True, endpoint)
