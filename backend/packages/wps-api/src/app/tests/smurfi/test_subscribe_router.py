"""Unit tests for smurfi subscribe endpoints."""

from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, patch

import app.main
import pytest
from app.routers.smurfi import (
    _get_spot_request_subscriber_emails,
    _spot_request_instance_has_changed,
)
from app.smurfi.nats_config import smurfi_spot_update_subject, stream_name, subjects
from fastapi.testclient import TestClient
from wps_shared.schemas.smurfi import SpotRequestInput, SpotRequestInstanceInput, SpotSubscriberData

DB_READ = "app.routers.smurfi.get_async_read_session_scope"
DB_WRITE = "app.routers.smurfi.get_async_write_session_scope"
SUBSCRIBE = "app.routers.smurfi.subscribe_to_spot_request"
UNSUBSCRIBE = "app.routers.smurfi.unsubscribe_from_spot_request"
GET_IDS = "app.routers.smurfi.get_subscribed_spot_request_ids"
GET_FORECASTS = "app.routers.smurfi.get_spot_forecasts_for_request"
GET_OR_CREATE_INSTANCE = "app.routers.smurfi.get_or_create_spot_request_instance"
GET_REQUEST = "app.routers.smurfi.get_spot_request_by_id"
CREATE_INSTANCE = "app.routers.smurfi.create_spot_request_instance"
UPDATE_REQUEST = "app.routers.smurfi.update_spot_request_details"
UPDATE_INSTANCE = "app.routers.smurfi.update_spot_request_instance_details"
SYNC_SUBSCRIBERS = "app.routers.smurfi.sync_spot_subscribers"
SYNC_GROUPS = "app.routers.smurfi.sync_spot_request_distribution_groups"


def _make_subscriber(status: str):
    return type("SpotSubscriber", (), {"subscriber_status": status})()


def _make_spot_request_instance(instance_id: int = 3):
    return type(
        "SpotRequestInstance",
        (),
        {
            "id": instance_id,
            "geographic_description": "Clearwater Valley",
            "aspect": "North",
            "elevation": 1000,
            "valley": None,
            "latitude": 48.5,
            "longitude": -123.5,
            "created_at": datetime(2026, 5, 21, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 5, 21, tzinfo=timezone.utc),
        },
    )()


def _make_spot_request():
    return type(
        "SpotRequestBase",
        (),
        {
            "id": 42,
            "request_reference": "WPS-test",
            "fire_number": ["V12345"],
            "fire_centre": 1,
            "status": "Requested",
            "requestor_name": "Original Owner",
            "requestor_idir": "owner_idir",
            "requestor_email": "owner@example.com",
            "request_frequency": ["Monday"],
            "request_type": "Full",
            "additional_information": "Original notes",
            "requested_at": datetime(2026, 5, 21, tzinfo=timezone.utc),
            "start_at": datetime(2026, 5, 22, tzinfo=timezone.utc),
            "end_at": datetime(2026, 5, 24, tzinfo=timezone.utc),
            "spot_request_instances": [_make_spot_request_instance()],
            "spot_forecasts": [],
            "spot_subscribers": [],
            "distribution_groups": [],
        },
    )()


def _make_spot_request_input(subscribers: list[SpotSubscriberData]):
    return SpotRequestInput(
        request_reference="WPS-test",
        fire_number=["V12345"],
        fire_centre=1,
        initial_instance=SpotRequestInstanceInput(
            geographic_description="Clearwater Valley",
            latitude=48.5,
            longitude=-123.5,
        ),
        requested_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
        start_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        subscribers=subscribers,
    )


def test_spot_request_subscriber_emails_include_requestor_once():
    assert _get_spot_request_subscriber_emails(
        _make_spot_request_input([SpotSubscriberData(email="owner@example.com")]),
        ["test@email.com"],
    ) == [
        "owner@example.com",
        "test@email.com",
    ]

    spot_request_input = _make_spot_request_input(
        [
            SpotSubscriberData(email="owner@example.com"),
            SpotSubscriberData(email="TEST@EMAIL.COM"),
        ]
    )

    assert _get_spot_request_subscriber_emails(spot_request_input, ["test@email.com"]) == [
        "owner@example.com",
        "TEST@EMAIL.COM",
    ]


def test_spot_request_instance_has_changed_detects_geographic_updates():
    existing = _make_spot_request_instance()

    assert not _spot_request_instance_has_changed(
        existing,
        SpotRequestInstanceInput(
            geographic_description="Clearwater Valley",
            aspect="North",
            elevation=1000,
            valley=None,
            latitude=48.5,
            longitude=-123.5,
        ),
    )

    assert not _spot_request_instance_has_changed(
        existing,
        SpotRequestInstanceInput(
            geographic_description="Clearwater Valley",
            aspect="North",
            elevation=1000,
            valley=None,
            latitude=48.5001,
            longitude=-123.5001,
        ),
    )

    assert _spot_request_instance_has_changed(
        existing,
        SpotRequestInstanceInput(
            geographic_description="Clearwater Valley",
            aspect="North",
            elevation=1000,
            valley=None,
            latitude=48.5003,
            longitude=-123.5,
        ),
    )

    assert _spot_request_instance_has_changed(
        existing,
        SpotRequestInstanceInput(
            geographic_description="New location description",
            aspect="North",
            elevation=1000,
            valley=None,
            latitude=48.5,
            longitude=-123.5,
        ),
    )


@pytest.mark.usefixtures("mock_jwt_decode")
def test_update_spot_request_updates_existing_request_instance():
    """PATCH spot request updates the request location instead of creating a new instance."""
    client = TestClient(app.main.app)
    spot_request = _make_spot_request()
    payload = {
        "fire_number": ["V12345"],
        "fire_centre": 1,
        "request_frequency": ["Monday"],
        "request_type": "Full",
        "additional_information": "Updated notes",
        "request_instance": {
            "geographic_description": "Updated location",
            "aspect": "North",
            "elevation": 1000,
            "valley": None,
            "latitude": 48.5003,
            "longitude": -123.5,
        },
        "start_at": "2026-05-22T00:00:00Z",
        "end_at": "2026-05-24T23:59:00Z",
        "subscribers": [],
        "distribution_group_ids": [],
    }

    with (
        patch(DB_WRITE),
        patch(GET_REQUEST, new_callable=AsyncMock, side_effect=[spot_request, spot_request]),
        patch(UPDATE_REQUEST, new_callable=AsyncMock, return_value=spot_request),
        patch(UPDATE_INSTANCE, new_callable=AsyncMock) as mock_update_instance,
        patch(CREATE_INSTANCE, new_callable=AsyncMock) as mock_create_instance,
        patch(SYNC_SUBSCRIBERS, new_callable=AsyncMock),
        patch(SYNC_GROUPS, new_callable=AsyncMock),
    ):
        response = client.patch("/api/smurfi/spot_requests/42", json=payload)

    assert response.status_code == 200
    mock_update_instance.assert_awaited_once()
    mock_create_instance.assert_not_awaited()


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


@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_spot_forecasts_returns_saved_forecasts():
    """GET spot forecasts returns forecasts and weather for a spot request."""
    client = TestClient(app.main.app)
    forecast_time = datetime(2026, 5, 21, 16, tzinfo=timezone.utc)
    descriptive_weather = [
        type(
            "SpotDescriptiveWeather",
            (),
            {
                "id": 7,
                "period": "Today",
                "temperature": 22,
                "relative_humidity": 35,
                "conditions": "Clear",
            },
        )()
    ]
    tabular_weather = [
        type(
            "SpotTabularWeather",
            (),
            {
                "id": 8,
                "forecast_time": forecast_time,
                "temperature": 20,
                "relative_humidity": 40,
                "wind": "SE 10-20 G 30-35",
                "probability_of_precipitation": 10,
                "precipitation_amount": 0,
            },
        )()
    ]
    forecast = type(
        "SpotForecast",
        (),
        {
            "id": 99,
            "spot_request_base_id": 42,
            "spot_request_instance_id": 3,
            "spot_request_instance": _make_spot_request_instance(),
            "forecaster_name": "Test Forecaster",
            "forecaster_email": "forecaster@example.com",
            "forecaster_phone": "250-555-0100",
            "synopsis": "High pressure.",
            "inversion_and_venting": "Good venting.",
            "outlook": "Dry.",
            "confidence": "High.",
            "forecast_type": "Mini",
            "fire_size": [12.5],
            "representative_station_codes": [1, 2],
            "created_at": forecast_time,
            "issued_at": forecast_time,
            "expires_at": None,
            "descriptive_weather": descriptive_weather,
            "tabular_weather": tabular_weather,
        },
    )()

    with (
        patch(DB_READ),
        patch(GET_FORECASTS, new_callable=AsyncMock, return_value=[forecast]),
    ):
        response = client.get("/api/smurfi/spot_requests/42/spot_forecasts")

    assert response.status_code == 200
    assert response.json()["spot_forecasts"][0]["id"] == 99
    assert response.json()["spot_forecasts"][0]["forecast_type"] == "Mini"
    assert response.json()["spot_forecasts"][0]["tabular_weather"][0]["wind"] == "SE 10-20 G 30-35"


PUBLISH = "app.routers.smurfi.publish"
CREATE_FORECAST = "app.routers.smurfi.create_spot_forecast"
CREATE_DW = "app.routers.smurfi._create_descriptive_weather"
CREATE_TW = "app.routers.smurfi._create_tabular_weather"
START_REQUEST = "app.routers.smurfi.start_requested_spot_request"

FORECAST_PAYLOAD = {
    "spot_request_base_id": 1,
    "spot_request_instance": {
        "geographic_description": "Clearwater Valley",
        "aspect": "North",
        "elevation": 1000,
        "valley": None,
        "latitude": 48.5,
        "longitude": -123.5,
    },
    "issued_at": "2026-05-21T16:00:00Z",
    "expires_at": None,
    "forecast_type": "Full",
    "forecaster_phone": "250-555-0100",
    "descriptive_weather": [],
    "tabular_weather": [],
}


@pytest.mark.usefixtures("mock_jwt_decode")
def test_create_spot_forecast_publishes_nats_message():
    """Creating a spot forecast publishes a smurfi.spot.update NATS message."""
    client = TestClient(app.main.app)
    mock_result = type("SpotForecast", (), {"id": 99})()
    with (
        patch(DB_WRITE),
        patch(
            CREATE_FORECAST, new_callable=AsyncMock, return_value=mock_result
        ) as mock_create_forecast,
        patch(
            GET_OR_CREATE_INSTANCE,
            new_callable=AsyncMock,
            return_value=_make_spot_request_instance(),
        ),
        patch(CREATE_DW, new_callable=AsyncMock, return_value=[]),
        patch(CREATE_TW, new_callable=AsyncMock, return_value=[]),
        patch(START_REQUEST, new_callable=AsyncMock) as mock_start_request,
        patch(PUBLISH, new_callable=AsyncMock) as mock_publish,
    ):
        response = client.post("/api/smurfi/spot_forecast", json=FORECAST_PAYLOAD)
    assert response.status_code == 200
    saved_forecast = mock_create_forecast.call_args.args[1]
    assert saved_forecast.forecaster_name == "test_username"
    assert saved_forecast.forecaster_email == "test@email.com"
    assert saved_forecast.forecaster_phone == "250-555-0100"
    assert saved_forecast.forecast_type == "Full"
    assert response.json()["spot_forecast"]["forecaster_phone"] == "250-555-0100"
    mock_start_request.assert_awaited_once_with(ANY, FORECAST_PAYLOAD["spot_request_base_id"])
    mock_publish.assert_called_once_with(
        stream=stream_name,
        subject=smurfi_spot_update_subject,
        payload=ANY,
        subjects=subjects,
    )
