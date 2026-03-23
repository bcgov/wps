"""Unit tests for FCM endpoints."""

from datetime import datetime
from unittest.mock import patch

import app.main
import pytest
from fastapi.testclient import TestClient
from wps_shared.db.models.fcm import PlatformEnum

DB_SESSION = "app.routers.fcm.get_async_write_session_scope"
GET_DEVICE_TOKEN = "app.routers.fcm.get_device_by_device_id"
SAVE_DEVICE_TOKEN = "app.routers.fcm.save_device_token"
GET_NOTIFICATION_SETTINGS = "app.routers.fcm.get_notification_settings_for_device"
UPSERT_NOTIFICATION_SETTINGS = "app.routers.fcm.upsert_notification_settings"
API_DEVICE_REGISTER = "/api/device/register"
API_DEVICE_UNREGISTER = "/api/device/unregister"
API_NOTIFICATION_SETTINGS = "/api/device/notification-settings"
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
    "method, endpoint, kwargs",
    [
        ("post", API_DEVICE_REGISTER, {"json": TEST_REGISTER_DEVICE_REQUEST}),
        ("post", API_DEVICE_UNREGISTER, {"json": TEST_UNREGISTER_DEVICE_REQUEST}),
        ("get", API_NOTIFICATION_SETTINGS, {"params": {"device_id": "test_device_id"}}),
        (
            "post",
            API_NOTIFICATION_SETTINGS,
            {"json": {"device_id": "test_device_id", "fire_zone_source_ids": ["1", "2"]}},
        ),
    ],
)
def test_endpoints_unauthorized(method, endpoint, kwargs, client: TestClient):
    """All device endpoints require authentication."""
    response = getattr(client, method)(endpoint, **kwargs)
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_register_device_success():
    """Test that device registration returns 200/OK."""
    client = TestClient(app.main.app)

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
@pytest.mark.parametrize(
    "request_data",
    [
        {"user_id": "test-user-123", "platform": "android"},  # missing token and device_id
        {
            "user_id": "test-user-123",
            "token": "test-fcm-token",
            "platform": "invalid-platform",
        },  # invalid platform
        {
            "user_id": "test-user-123",
            "token": "short",
            "platform": "android",
            "device_id": "test_device_id",
        },  # token too short
        {
            "user_id": "test-user-123",
            "token": "test-fcm-token-456",
            "platform": "android",
        },  # missing device_id
    ],
)
def test_register_device_invalid_request_returns_422(request_data):
    """Invalid register requests return 422."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        response = client.post(API_DEVICE_REGISTER, json=request_data)
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


@pytest.mark.usefixtures("mock_jwt_decode")
def test_unregister_device_success():
    """Test that device unregistration returns 200/OK."""
    client = TestClient(app.main.app)

    request_data = {"token": "test-fcm-token-456"}

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch("app.routers.fcm.update_device_token_is_active"):
            response = client.post(API_DEVICE_UNREGISTER, json=request_data)

            assert response.status_code == 200
            assert response.json()["success"] == True


@pytest.mark.usefixtures("mock_jwt_decode")
def test_unregister_device_missing_token():
    """Test that missing token field returns 422."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        response = client.post(API_DEVICE_UNREGISTER, json={})
        assert response.status_code == 422


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize("subscribed_ids", [[], ["10", "20", "30"]])
def test_get_notification_settings(subscribed_ids):
    """GET notification settings returns the device's subscribed fire zone source identifiers."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(GET_NOTIFICATION_SETTINGS, return_value=subscribed_ids):
            response = client.get(API_NOTIFICATION_SETTINGS, params={"device_id": "test_device_id"})

            assert response.status_code == 200
            assert response.json() == {"fire_zone_source_ids": subscribed_ids}


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize(
    "payload",
    [
        {"fire_zone_source_ids": ["1", "2"]},  # missing device_id
        {"device_id": "test_device_id"},  # missing fire_zone_source_ids
    ],
)
def test_post_notification_settings_invalid_request_returns_422(payload):
    """POST notification settings with missing required fields returns 422."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        response = client.post(API_NOTIFICATION_SETTINGS, json=payload)
        assert response.status_code == 422


@pytest.mark.usefixtures("mock_jwt_decode")
def test_post_notification_settings_unknown_device_returns_404():
    """POST notification settings returns 404 when the device_id is not registered."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(UPSERT_NOTIFICATION_SETTINGS, return_value=False):
            response = client.post(
                API_NOTIFICATION_SETTINGS,
                json={"device_id": "unknown_device", "fire_zone_source_ids": ["1"]},
            )
            assert response.status_code == 404


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize("fire_zone_source_ids", [["5", "10"], []])
def test_post_notification_settings_success(fire_zone_source_ids):
    """POST notification settings replaces subscriptions and returns the updated list."""
    client = TestClient(app.main.app)

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with (
            patch(UPSERT_NOTIFICATION_SETTINGS, return_value=True),
            patch(GET_NOTIFICATION_SETTINGS, return_value=fire_zone_source_ids),
        ):
            response = client.post(
                API_NOTIFICATION_SETTINGS,
                json={
                    "device_id": "test_device_id",
                    "fire_zone_source_ids": fire_zone_source_ids,
                },
            )

            assert response.status_code == 200
            assert response.json() == {"fire_zone_source_ids": fire_zone_source_ids}
