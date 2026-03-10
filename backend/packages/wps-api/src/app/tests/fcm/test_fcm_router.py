"""Unit tests for FCM endpoints."""

from datetime import datetime
from unittest.mock import patch

import app.main
import pytest
from app.fcm.schema import RegisterDeviceRequest
from fastapi.testclient import TestClient
from wps_shared.db.models.fcm import PlatformEnum

DB_SESSION = "app.routers.fcm.get_async_write_session_scope"
GET_DEVICE_TOKEN = "app.routers.fcm.get_device_by_device_id"
SAVE_DEVICE_TOKEN = "app.routers.fcm.save_device_token"
API_DEVICE_REGISTER = "/api/device/register"
API_DEVICE_UNREGISTER = "/api/device/unregister"
MOCK_DEVICE_TOKEN = "abcdefghijklmonp"
TEST_REGISTER_DEVICE_REQUEST = {
    "user_id": "test_idir",
    "device_id": "test_device_id",
    "token": MOCK_DEVICE_TOKEN,
    "platform": PlatformEnum.android.value,
}
TEST_UNREGISTER_DEVICE_REQUEST = {"token": MOCK_DEVICE_TOKEN}


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures("mock_client_session")
@pytest.mark.parametrize(
    "endpoint, payload",
    [
        (API_DEVICE_REGISTER, TEST_REGISTER_DEVICE_REQUEST),
        (API_DEVICE_UNREGISTER, TEST_UNREGISTER_DEVICE_REQUEST),
    ],
)
def test_get_endpoints_unauthorized(endpoint: str, payload, client: TestClient):
    """Forbidden to get fire zone areas when unauthorized"""

    response = client.post(endpoint, json=payload)
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_success():
    """Test that device registration returns 200/OK."""
    client = TestClient(app.main.app)

    # Test data
    request_data = {
        "user_id": "test-user-123",
        "device_id": "test_device_id",
        "token": "test-fcm-token-456",
        "platform": "android",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with (
            patch(GET_DEVICE_TOKEN, return_value=None),
            patch(SAVE_DEVICE_TOKEN),
        ):
            response = client.post(API_DEVICE_REGISTER, json=request_data)

            assert response.status_code == 200
            assert response.json()["success"] == True
            assert response.headers["content-type"] == "application/json"

@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_already_exists():
    """Test that existing device registration updates successfully."""
    client = TestClient(app.main.app)

    request_data = {
        "user_id": "test-user-123",
        "device_id": "test_device_id",
        "token": "existing-fcm-token",
        "platform": "ios",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        existing_device = type(
            "",
            (object,),
            {
                "is_active": False,
                "device_id": "test_device_id",
                "token": "existing-fcm-token",
                "updated_at": datetime(2026, 1, 1),
            },
        )()

        with (
            patch(GET_DEVICE_TOKEN, return_value=existing_device),
            patch(SAVE_DEVICE_TOKEN) as mock_save,
        ):
            response = client.post(API_DEVICE_REGISTER, json=request_data)

            assert response.status_code == 200
            assert response.json()["success"] == True
            assert existing_device.is_active == True  # Should be updated
            mock_save.assert_not_called()  # Should not call save for existing device

@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_missing_fields():
    """Test that missing fields in registration request returns 422."""
    client = TestClient(app.main.app)

    # Missing 'token' field which is required
    request_data = {"user_id": "test-user-123", "platform": "android"}

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        response = client.post(API_DEVICE_REGISTER, json=request_data)

        assert response.status_code == 422

@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_invalid_platform():
    """Test that invalid platform returns 422."""
    client = TestClient(app.main.app)

    request_data = {
        "user_id": "test-user-123",
        "token": "test-fcm-token",
        "platform": "invalid-platform",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        response = client.post(API_DEVICE_REGISTER, json=request_data)

        assert response.status_code == 422

@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_short_token():
    """Test that short token returns 422."""
    client = TestClient(app.main.app)

    request_data = {
        "user_id": "test-user-123",
        "token": "short",  # Less than 10 characters
        "platform": "android",
        "device_id": "test_device_id",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        response = client.post(API_DEVICE_REGISTER, json=request_data)

        assert response.status_code == 422


@pytest.mark.usefixtures("mock_jwt_decode")
def test_missing_device_id_returns_422():
    """Test that a missing device_id returns 422."""
    client = TestClient(app.main.app)

    request_data = {
        "user_id": "test-user-123",
        "token": "short",  # Less than 10 characters
        "platform": "android",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        response = client.post(API_DEVICE_REGISTER, json=request_data)

        assert response.status_code == 422

@pytest.mark.usefixtures("mock_jwt_decode")
def test_unregister_device_success():
    """Test that device unregistration returns 200/OK."""
    client = TestClient(app.main.app)

    request_data = {"token": "test-fcm-token-456"}

    with patch("app.routers.fcm.get_async_write_session_scope") as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch("app.routers.fcm.update_device_token_is_active"):
            response = client.post("/api/device/unregister", json=request_data)

            assert response.status_code == 200
            assert response.json()["success"] == True

@pytest.mark.usefixtures("mock_jwt_decode")
def test_unregister_device_missing_token():
    """Test that missing token field returns 422."""
    client = TestClient(app.main.app)

    request_data = {}

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value

        response = client.post("/api/device/unregister", json=request_data)

        assert response.status_code == 422

@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_without_user_id():
    """Test that device registration without user_id is allowed (null user)."""
    client = TestClient(app.main.app)

    request_data = {
        "token": "test-fcm-token-789",
        "platform": "android",
        "device_id": "test_device_id",
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with (
            patch(GET_DEVICE_TOKEN, return_value=None),
            patch(SAVE_DEVICE_TOKEN),
        ):
            response = client.post(API_DEVICE_REGISTER, json=request_data)

            assert response.status_code == 200
            assert response.json()["success"] == True
