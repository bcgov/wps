import os
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from wps_shared.db.models.fcm import PlatformEnum
from wps_shared.db.models.psu import FireCentre
from wps_shared.run_type import RunType

DB_SESSION = "app.routers.fcm.get_async_write_session_scope"
READ_DB_SESSION = "app.routers.fcm.get_async_read_session_scope"
GET_DEVICE_TOKEN = "app.routers.fcm.get_device_by_device_id"
SAVE_DEVICE_TOKEN = "app.routers.fcm.save_device_token"
UPDATE_DEVICE_TOKEN = "app.routers.fcm.update_device_token_is_active"
GET_NOTIFICATION_SETTINGS = "app.routers.fcm.get_notification_settings_for_device"
UPSERT_NOTIFICATION_SETTINGS = "app.routers.fcm.upsert_notification_settings"


@pytest.fixture()
def client():
    from app.asa_go_main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def before_each():
    os.environ["DISABLE_ASA_GO_DATE_VALIDATION"] = "False"


@patch("app.routers.psu.fetch_fire_centres")
def test_public_psu_fire_centres_endpoint(mock_fetch_fire_centres, client: TestClient):
    mock_fetch_fire_centres.return_value = [
        FireCentre(id=1, name="Coastal Fire Centre"),
        FireCentre(id=2, name="Northwest Fire Centre"),
    ]

    response = client.get("/api/asa-go/fire-centres")

    assert response.status_code == 200
    assert response.json() == {
        "fire_centres": [
            {"id": 1, "name": "Coastal Fire Centre"},
            {"id": 2, "name": "Northwest Fire Centre"},
        ]
    }


@patch("app.routers.fba.get_most_recent_run_datetime_for_date")
def test_public_latest_sfms_run_datetime_endpoint(mock_latest_run_parameter, client: TestClient):
    mock_latest_run_parameter.return_value = type(
        "",
        (),
        {
            "for_date": date(2025, 8, 26),
            "run_datetime": datetime(2025, 8, 26, 15, 1, 47, 340947, tzinfo=timezone.utc),
            "run_type": RunType.FORECAST.value,
        },
    )()

    with patch(
        "app.routers.asa_go.get_vancouver_now",
        return_value=datetime(2025, 8, 26, 12, tzinfo=timezone.utc),
    ):
        response = client.get("/api/asa-go/latest-sfms-run-datetime/2025-08-26")

    assert response.status_code == 200
    assert response.json() == {
        "run_parameter": {
            "for_date": "2025-08-26",
            "run_datetime": "2025-08-26T15:01:47.340947Z",
            "run_type": RunType.FORECAST.value,
        }
    }


@patch("app.routers.fba.get_most_recent_run_datetime_for_date")
def test_public_latest_sfms_run_datetime_rejects_past_dates(
    mock_latest_run_parameter, client: TestClient
):
    with patch(
        "app.routers.asa_go.get_vancouver_now",
        return_value=datetime(2025, 8, 26, 12, tzinfo=timezone.utc),
    ):
        response = client.get("/api/asa-go/latest-sfms-run-datetime/2025-08-25")

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "ASA Go only accepts dates on or after 2025-08-26. Rejected: 2025-08-25"
    )
    mock_latest_run_parameter.assert_not_called()


@patch("app.routers.fba.get_most_recent_run_datetime_for_date_range")
def test_public_latest_sfms_run_datetime_range_rejects_past_dates(
    mock_latest_run_parameter_range, client: TestClient
):
    with patch(
        "app.routers.asa_go.get_vancouver_now",
        return_value=datetime(2025, 8, 26, 12, tzinfo=timezone.utc),
    ):
        response = client.get("/api/asa-go/latest-sfms-run-parameters/2025-08-25/2025-08-26")

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "ASA Go only accepts dates on or after 2025-08-26. Rejected: 2025-08-25"
    )
    mock_latest_run_parameter_range.assert_not_called()


def test_public_register_device_endpoint(client: TestClient):
    request_data = {
        "user_id": "test-user-123",
        "device_id": "test_device_id",
        "token": "test-fcm-token-456",
        "platform": PlatformEnum.android.value,
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with (
            patch(GET_DEVICE_TOKEN, return_value=None),
            patch(SAVE_DEVICE_TOKEN),
        ):
            response = client.post("/api/asa-go/device/register", json=request_data)

            assert response.status_code == 200
            assert response.json() == {"success": True}


def test_public_unregister_device_endpoint(client: TestClient):
    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(UPDATE_DEVICE_TOKEN, return_value=True):
            response = client.post(
                "/api/asa-go/device/unregister",
                json={"token": "test-fcm-token-456"},
            )

            assert response.status_code == 200
            assert response.json() == {"success": True}


def test_public_get_notification_settings_endpoint(client: TestClient):
    with patch(READ_DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with patch(GET_NOTIFICATION_SETTINGS, return_value=["zone-1", "zone-2"]):
            response = client.get(
                "/api/asa-go/device/notification-settings",
                params={"device_id": "test_device_id"},
            )

            assert response.status_code == 200
            assert response.json() == {"fire_zone_source_ids": ["zone-1", "zone-2"]}


def test_public_update_notification_settings_endpoint(client: TestClient):
    request_data = {
        "device_id": "test_device_id",
        "fire_zone_source_ids": ["zone-1", "zone-2"],
    }

    with patch(DB_SESSION) as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value
        with (
            patch(UPSERT_NOTIFICATION_SETTINGS, return_value=True),
            patch(GET_NOTIFICATION_SETTINGS, return_value=["zone-1", "zone-2"]),
        ):
            response = client.post(
                "/api/asa-go/device/notification-settings",
                json=request_data,
            )

            assert response.status_code == 200
            assert response.json() == {"fire_zone_source_ids": ["zone-1", "zone-2"]}
