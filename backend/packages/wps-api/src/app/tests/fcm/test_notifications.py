"""Unit tests for FCM notification logic."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.fcm.notifications import (
    build_notification_content,
    build_notification_title,
    handle_fcm_response,
    trigger_notifications,
)
from firebase_admin import messaging
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum

GET_APP = "app.fcm.notifications.firebase_admin.get_app"
GET_ZONES = "app.fcm.notifications.get_zones_with_advisories"
GET_TOKENS = "app.fcm.notifications.get_device_tokens_for_zone"
UPDATE_TOKENS = "app.fcm.notifications.update_device_tokens_are_active"
SEND_MULTICAST = "app.fcm.notifications.messaging.send_each_for_multicast"


@pytest.mark.parametrize(
    "for_date, placename_label, expected",
    [
        (
            date(2026, 4, 1),
            "K2-Kamloops Zone (Kamloops)",
            "Wed, April 1 - An advisory has been issued for K2-Kamloops Zone (Kamloops)",
        ),
        (
            date(2026, 3, 23),
            "C5-Chilcotin Zone",
            "Mon, March 23 - An advisory has been issued for C5-Chilcotin Zone",
        ),
    ],
)
def test_build_notification_content(for_date, placename_label, expected):
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1,
        source_identifier="42",
        placename_label=placename_label,
        status="advisory",
    )
    assert build_notification_content(zone, for_date) == expected


@pytest.mark.parametrize(
    "placename_label, expected",
    [
        ("K2-Kamloops Zone (Kamloops)", "Behaviour Advisory, K2"),
        ("C5-Chilcotin Zone", "Behaviour Advisory, C5"),
    ],
)
def test_build_notification_title(placename_label, expected):
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1,
        source_identifier="42",
        placename_label=placename_label,
        status="advisory",
    )
    assert build_notification_title(zone) == expected


@pytest.mark.anyio
async def test_trigger_notifications_skips_forecast():
    """Forecast run type should return immediately without querying anything."""
    session = AsyncMock()
    with patch(GET_ZONES) as mock_get_zones:
        await trigger_notifications(
            session, RunTypeEnum.forecast, datetime(2026, 4, 1), date(2026, 4, 1)
        )
        mock_get_zones.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_no_zones():
    """No zones with advisories means no notifications sent."""
    session = AsyncMock()
    with patch(GET_ZONES, return_value=[]), patch(SEND_MULTICAST) as mock_send:
        await trigger_notifications(
            session, RunTypeEnum.actual, datetime(2026, 4, 1), date(2026, 4, 1)
        )
        mock_send.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_no_subscribers():
    """Zones with advisories but no subscribed devices send no notifications."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=[]),
        patch(SEND_MULTICAST) as mock_send,
    ):
        await trigger_notifications(
            session, RunTypeEnum.actual, datetime(2026, 4, 1), date(2026, 4, 1)
        )
        mock_send.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_sends_multicast():
    """Zones with advisories and subscribers triggers a multicast send."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = ["token_a", "token_b"]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_APP),
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_MULTICAST, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
    ):
        await trigger_notifications(
            session, RunTypeEnum.actual, datetime(2026, 4, 1), date(2026, 4, 1)
        )
        mock_send.assert_called_once()
        call_arg = mock_send.call_args[0][0]
        assert call_arg.tokens == tokens
        assert "Kamloops" in call_arg.notification.title
        assert "Kamloops" in call_arg.notification.body


@pytest.mark.anyio
async def test_trigger_notifications_calls_handle_response():
    """handle_fcm_response is called with the correct arguments after send."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = ["token_a"]
    for_date = date(2026, 4, 1)
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_APP),
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_MULTICAST, return_value=mock_response),
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
    ):
        await trigger_notifications(session, RunTypeEnum.actual, datetime(2026, 4, 1), for_date)
        mock_handle.assert_called_once_with(session, for_date, "Kamloops", tokens, mock_response)


@pytest.mark.anyio
async def test_trigger_notifications_continues_on_send_failure():
    """A send failure for one zone does not abort remaining zones."""
    session = AsyncMock()
    zone_a = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="1", placename_label="Zone A", status="advisory"
    )
    zone_b = ZoneAdvisoryStatus(
        advisory_shape_id=2, source_identifier="2", placename_label="Zone B", status="advisory"
    )
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_APP),
        patch(GET_ZONES, return_value=[zone_a, zone_b]),
        patch(GET_TOKENS, return_value=["token"]),
        patch(SEND_MULTICAST, side_effect=[Exception("FCM error"), mock_response]) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
    ):
        await trigger_notifications(
            session, RunTypeEnum.actual, datetime(2026, 4, 1), date(2026, 4, 1)
        )
        assert mock_send.call_count == 2
        mock_handle.assert_called_once()  # Only zone_b succeeded


@pytest.mark.anyio
async def test_build_notification_title_none_placename():
    """build_notification_title does not crash when placename_label is None."""
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label=None, status="advisory"
    )
    assert build_notification_title(zone) == "Behaviour Advisory, Unknown Zone"


@pytest.mark.anyio
async def test_handle_fcm_response_all_success():
    """All successful responses — update_device_tokens_are_active is not called."""
    session = AsyncMock()
    resp_a = MagicMock(success=True)
    resp_b = MagicMock(success=True)
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 0
    response.responses = [resp_a, resp_b]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(session, date(2026, 4, 1), "Kamloops", ["t1", "t2"], response)
        mock_update.assert_not_called()


@pytest.mark.anyio
async def test_handle_fcm_response_partial_failure():
    """Successful tokens are marked active; failed tokens are marked inactive."""
    session = AsyncMock()
    resp_ok = MagicMock(success=True)
    resp_fail = MagicMock(success=False)
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 1
    response.responses = [resp_ok, resp_fail]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(
            session, date(2026, 4, 1), "Kamloops", ["token_good", "token_bad"], response
        )
        mock_update.assert_any_call(session, ["token_good"], True)
        mock_update.assert_any_call(session, ["token_bad"], False)


@pytest.mark.anyio
async def test_handle_fcm_response_all_failure():
    """All tokens failed — all are marked inactive."""
    session = AsyncMock()
    resp_fail = MagicMock(success=False)
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 1
    response.responses = [resp_fail]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(session, date(2026, 4, 1), "Kamloops", ["token_bad"], response)
        mock_update.assert_any_call(session, [], True)
        mock_update.assert_any_call(session, ["token_bad"], False)
