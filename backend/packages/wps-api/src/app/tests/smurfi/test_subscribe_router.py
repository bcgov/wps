"""Unit tests for smurfi subscribe endpoints."""
<<<<<<< HEAD
from unittest.mock import ANY, AsyncMock, patch

import app.main
from app.smurfi.nats_config import smurfi_spot_update_subject, stream_name, subjects
=======
from unittest.mock import patch, AsyncMock

import app.main
>>>>>>> f366ad684 (feat: add POST /smurfi/spots/{id}/subscribe and GET /smurfi/subscriptions)
import pytest
from fastapi.testclient import TestClient

DB_READ = "app.routers.smurfi.get_async_read_session_scope"
DB_WRITE = "app.routers.smurfi.get_async_write_session_scope"
TOGGLE = "app.routers.smurfi.toggle_subscription"
GET_IDS = "app.routers.smurfi.get_subscribed_spot_request_ids"


def _make_subscriber(status: str):
    return type("SpotSubscriber", (), {"subscriber_status": status})()


@pytest.mark.usefixtures("mock_jwt_decode")
def test_subscribe_creates_active_subscription():
    """POST subscribe returns active status when user was not subscribed."""
    client = TestClient(app.main.app)
<<<<<<< HEAD
    with patch(DB_WRITE):
=======
    with patch(DB_WRITE) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
>>>>>>> f366ad684 (feat: add POST /smurfi/spots/{id}/subscribe and GET /smurfi/subscriptions)
        with patch(TOGGLE, new_callable=AsyncMock, return_value=_make_subscriber("active")):
            response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 200
    assert response.json()["subscriber_status"] == "active"


@pytest.mark.usefixtures("mock_jwt_decode")
def test_subscribe_toggle_to_inactive():
    """POST subscribe returns inactive status when toggling off."""
    client = TestClient(app.main.app)
<<<<<<< HEAD
    with patch(DB_WRITE):
=======
    with patch(DB_WRITE) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
>>>>>>> f366ad684 (feat: add POST /smurfi/spots/{id}/subscribe and GET /smurfi/subscriptions)
        with patch(TOGGLE, new_callable=AsyncMock, return_value=_make_subscriber("inactive")):
            response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 200
    assert response.json()["subscriber_status"] == "inactive"


def test_subscribe_requires_auth():
    """POST subscribe returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_subscriptions_returns_ids():
    """GET subscriptions returns the list of subscribed spot_request_ids."""
    client = TestClient(app.main.app)
<<<<<<< HEAD
    with patch(DB_READ):
=======
    with patch(DB_READ) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
>>>>>>> f366ad684 (feat: add POST /smurfi/spots/{id}/subscribe and GET /smurfi/subscriptions)
        with patch(GET_IDS, new_callable=AsyncMock, return_value=[1, 5, 10]):
            response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 200
    assert response.json() == {"spot_request_ids": [1, 5, 10]}


def test_get_subscriptions_requires_auth():
    """GET subscriptions returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 401
<<<<<<< HEAD


PUBLISH = "app.routers.smurfi.publish"
CREATE_FORECAST = "app.routers.smurfi.create_spot_forecast"
UPSERT_DW = "app.routers.smurfi._upsert_descriptive_weather"
UPSERT_TW = "app.routers.smurfi._upsert_tabular_weather"

FORECAST_PAYLOAD = {
    "spot_request_id": 1,
    "forecaster_name": "Test Forecaster",
    "forecaster_email": "forecaster@example.com",
    "descriptive_weather": [],
    "tabular_weather": [],
}


@pytest.mark.usefixtures("mock_jwt_decode")
def test_upsert_spot_forecast_publishes_nats_message():
    """Saving a spot forecast publishes a smurfi.spot.update NATS message."""
    client = TestClient(app.main.app)
    mock_result = type("SpotForecast", (), {"id": 99})()
    with (
        patch(DB_WRITE),
        patch(CREATE_FORECAST, new_callable=AsyncMock, return_value=mock_result),
        patch(UPSERT_DW, new_callable=AsyncMock, return_value=[]),
        patch(UPSERT_TW, new_callable=AsyncMock, return_value=[]),
        patch(PUBLISH, new_callable=AsyncMock) as mock_publish,
    ):
        response = client.post("/api/smurfi/spot_forecast", json=FORECAST_PAYLOAD)
    assert response.status_code == 200
    mock_publish.assert_called_once_with(
        stream=stream_name,
        subject=smurfi_spot_update_subject,
        payload=ANY,
        subjects=subjects,
    )
=======
>>>>>>> f366ad684 (feat: add POST /smurfi/spots/{id}/subscribe and GET /smurfi/subscriptions)
