"""Unit tests for smurfi subscribe endpoints."""

from unittest.mock import ANY, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import app.main
from app.smurfi.nats_config import smurfi_spot_update_subject, stream_name, subjects

DB_READ = "app.routers.smurfi.get_async_read_session_scope"
DB_WRITE = "app.routers.smurfi.get_async_write_session_scope"
SUBSCRIBE = "app.routers.smurfi.subscribe_to_spot_request"
UNSUBSCRIBE = "app.routers.smurfi.unsubscribe_from_spot_request"
GET_IDS = "app.routers.smurfi.get_subscribed_spot_request_ids"


def _make_subscriber(status: str):
    return type("SpotSubscriber", (), {"subscriber_status": status})()


@pytest.mark.usefixtures("mock_jwt_decode")
def test_subscribe_returns_active_status():
    """POST subscribe returns active status."""
    client = TestClient(app.main.app)
    with patch(DB_WRITE):
        with patch(SUBSCRIBE, new_callable=AsyncMock, return_value=_make_subscriber("active")):
            response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 200
    assert response.json()["subscriber_status"] == "active"


def test_subscribe_requires_auth():
    """POST subscribe returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_unsubscribe_returns_204():
    """DELETE subscribe returns 204 when subscription exists."""
    client = TestClient(app.main.app)
    with patch(DB_WRITE):
        with patch(UNSUBSCRIBE, new_callable=AsyncMock, return_value=_make_subscriber("inactive")):
            response = client.delete("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 204


@pytest.mark.usefixtures("mock_jwt_decode")
def test_unsubscribe_returns_404_when_not_subscribed():
    """DELETE subscribe returns 404 when no subscription exists."""
    client = TestClient(app.main.app)
    with patch(DB_WRITE):
        with patch(UNSUBSCRIBE, new_callable=AsyncMock, return_value=None):
            response = client.delete("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 404


def test_unsubscribe_requires_auth():
    """DELETE subscribe returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.delete("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_subscriptions_returns_ids():
    """GET subscriptions returns the list of subscribed spot_request_ids."""
    client = TestClient(app.main.app)
    with patch(DB_READ):
        with patch(GET_IDS, new_callable=AsyncMock, return_value=[1, 5, 10]):
            response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 200
    assert response.json() == {"spot_request_ids": [1, 5, 10]}


def test_get_subscriptions_requires_auth():
    """GET subscriptions returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 401


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
