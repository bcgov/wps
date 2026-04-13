"""Unit tests for FCM notification logic."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.fcm.notifications import (
    build_fcm_message,
    build_notification_content,
    build_notification_title,
    handle_fcm_response,
    trigger_notifications,
)
from firebase_admin import exceptions as firebase_exceptions
from firebase_admin import messaging
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum

GET_ZONES = "app.fcm.notifications.get_zones_with_advisories"
GET_TOKENS = "app.fcm.notifications.get_device_tokens_for_zone"
UPDATE_TOKENS = "app.fcm.notifications.update_device_tokens_are_active"
SEND_MULTICAST = "app.fcm.notifications.messaging.send_each_for_multicast"
GET_VANCOUVER_NOW = "app.fcm.notifications.get_vancouver_now"

FOR_DATE = date(2026, 4, 1)
RUN_GET_VANCOUVER_NOW = datetime(2026, 4, 1)


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
        ("K2-Kamloops Zone (Kamloops)", "Fire Behaviour Advisory, K2"),
        ("C5-Chilcotin Zone", "Fire Behaviour Advisory, C5"),
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


ENVIRONMENT = "app.fcm.notifications.config"

@pytest.mark.anyio
@pytest.mark.parametrize(
    "environment, vancouver_hour, expect_skipped",
    [
        ("production", 15, True),   # afternoon >= 12 in prod → skip
        ("production", 12, True),   # noon == 12 in prod → skip (boundary)
        ("production", 8, False),   # morning < 12 in prod → proceed
        ("development", 15, False), # afternoon outside prod → proceed
        ("development", 8, False),  # morning outside prod → proceed
    ],
)
async def test_trigger_notifications_afternoon_filter(environment, vancouver_hour, expect_skipped):
    """Afternoon Vancouver time (hour >= 12) is skipped only in production."""
    session = AsyncMock()
    with (
        patch(GET_ZONES, return_value=[]) as mock_get_zones,
        patch(GET_VANCOUVER_NOW) as mock_now,
        patch(ENVIRONMENT) as mock_config,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        mock_now.return_value.hour = vancouver_hour
        mock_config.get.return_value = environment
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        if expect_skipped:
            mock_get_zones.assert_not_called()
        else:
            mock_get_zones.assert_called_once()


@pytest.mark.anyio
async def test_trigger_notifications_skips_actual():
    """Actual run type should return immediately without querying anything."""
    session = AsyncMock()
    with patch(GET_ZONES) as mock_get_zones, patch(GET_VANCOUVER_NOW) as mock_now:
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.actual, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_get_zones.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_skips_past_date():
    """for_date in the past should return without querying anything."""
    session = AsyncMock()
    with patch(GET_ZONES) as mock_get_zones, patch(GET_VANCOUVER_NOW) as mock_now:
        mock_now.return_value.date.return_value = date(2026, 4, 2)
        await trigger_notifications(session, RunTypeEnum.actual, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_get_zones.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_no_zones():
    """No zones with advisories means no notifications sent."""
    session = AsyncMock()
    with (
        patch(GET_ZONES, return_value=[]),
        patch(SEND_MULTICAST) as mock_send,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
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
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_send.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_sends_multicast():
    """Zones with advisories and subscribers triggers a multicast send."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="K2-Kamloops Zone (Kamloops)", status="advisory"
    )
    tokens = ["token_a", "token_b"]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_MULTICAST, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_send.assert_called_once()
        call_arg = mock_send.call_args[0][0]
        assert call_arg.tokens == tokens
        assert call_arg.notification.title == "Fire Behaviour Advisory, K2"
        assert "K2-Kamloops Zone (Kamloops)" in call_arg.notification.body


@pytest.mark.anyio
async def test_trigger_notifications_batches_tokens_over_limit():
    """Token lists larger than FCM_BATCH_SIZE are split into multiple sends."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = [f"token_{i}" for i in range(501)]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_MULTICAST, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        assert mock_send.call_count == 2
        first_batch = mock_send.call_args_list[0][0][0].tokens
        second_batch = mock_send.call_args_list[1][0][0].tokens
        assert len(first_batch) == 500
        assert len(second_batch) == 1
        assert first_batch + second_batch == tokens


@pytest.mark.anyio
async def test_trigger_notifications_calls_handle_response():
    """handle_fcm_response is called with the correct arguments after send."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = ["token_a"]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_MULTICAST, return_value=mock_response),
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_handle.assert_called_once_with(session, FOR_DATE, "Kamloops", tokens, mock_response)


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
        patch(GET_ZONES, return_value=[zone_a, zone_b]),
        patch(GET_TOKENS, return_value=["token"]),
        patch(
            SEND_MULTICAST,
            side_effect=[firebase_exceptions.UnavailableError("FCM error", None), mock_response],
        ) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        assert mock_send.call_count == 2
        mock_handle.assert_called_once()  # Only zone_b succeeded


@pytest.mark.anyio
async def test_trigger_notifications_skips_zone_with_missing_placename():
    """Zones with no placename_label are skipped — no tokens fetched, no notification sent."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, source_identifier="42", placename_label=None, status="advisory"
    )
    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS) as mock_get_tokens,
        patch(SEND_MULTICAST) as mock_send,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_get_tokens.assert_not_called()
        mock_send.assert_not_called()


@pytest.mark.anyio
async def test_handle_fcm_response_all_success():
    """All successful responses — no tokens deactivated."""
    session = AsyncMock()
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 0
    response.responses = [MagicMock(success=True), MagicMock(success=True)]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(session, date(2026, 4, 1), "Kamloops", ["t1", "t2"], response)
        mock_update.assert_not_called()


@pytest.mark.anyio
async def test_handle_fcm_response_permanent_failure_deactivates_token():
    """UnregisteredError tokens are permanently deactivated."""
    session = AsyncMock()
    resp_ok = MagicMock(success=True)
    resp_fail = MagicMock(
        success=False, exception=messaging.UnregisteredError("token expired", None)
    )
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 1
    response.responses = [resp_ok, resp_fail]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(
            session, date(2026, 4, 1), "Kamloops", ["token_good", "token_bad"], response
        )
        mock_update.assert_called_once_with(session, ["token_bad"], False)


@pytest.mark.anyio
async def test_handle_fcm_response_transient_failure_does_not_deactivate():
    """Transient failures (non-UnregisteredError) do not deactivate the token."""
    session = AsyncMock()
    resp_fail = MagicMock(
        success=False, exception=firebase_exceptions.UnavailableError("server down", None)
    )
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 1
    response.responses = [resp_fail]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(session, date(2026, 4, 1), "Kamloops", ["token_ok"], response)
        mock_update.assert_not_called()


ZONE = ZoneAdvisoryStatus(
    advisory_shape_id=1,
    source_identifier="42",
    placename_label="K2-Kamloops Zone (Kamloops)",
    status="advisory",
)
TOKENS = ["token_a", "token_b", "token_c"]
MSG_DATE = date(2026, 4, 1)
FIXED_NOW = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
EXPECTED_APNS_EXPIRATION = str(int((FIXED_NOW + timedelta(days=2)).timestamp()))


def test_build_fcm_message_notification_content():
    msg = build_fcm_message(MSG_DATE, ZONE, TOKENS)
    assert isinstance(msg, messaging.MulticastMessage)
    assert msg.tokens == TOKENS
    assert msg.notification.title == "Fire Behaviour Advisory, K2"
    assert "K2-Kamloops Zone (Kamloops)" in msg.notification.body
    assert "Wed, April 1" in msg.notification.body


def test_build_fcm_message_platform_tags():
    with patch("app.fcm.notifications.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_NOW
        msg = build_fcm_message(MSG_DATE, ZONE, TOKENS)

    assert msg.android.notification.tag == "advisory-42"
    assert msg.apns.payload.aps.thread_id == msg.android.notification.tag
    assert msg.android.ttl == timedelta(days=2)
    assert msg.apns.headers["apns-expiration"] == EXPECTED_APNS_EXPIRATION
