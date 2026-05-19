"""Unit tests for smurfi subscribe endpoints."""
from unittest.mock import patch, AsyncMock

import app.main
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
    with patch(DB_WRITE) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(TOGGLE, new_callable=AsyncMock, return_value=_make_subscriber("active")):
            response = client.post("/api/smurfi/spots/42/subscribe")
    assert response.status_code == 200
    assert response.json()["subscriber_status"] == "active"


@pytest.mark.usefixtures("mock_jwt_decode")
def test_subscribe_toggle_to_inactive():
    """POST subscribe returns inactive status when toggling off."""
    client = TestClient(app.main.app)
    with patch(DB_WRITE) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
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
    with patch(DB_READ) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(GET_IDS, new_callable=AsyncMock, return_value=[1, 5, 10]):
            response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 200
    assert response.json() == {"spot_request_ids": [1, 5, 10]}


def test_get_subscriptions_requires_auth():
    """GET subscriptions returns 401 when not authenticated."""
    client = TestClient(app.main.app)
    response = client.get("/api/smurfi/subscriptions")
    assert response.status_code == 401
