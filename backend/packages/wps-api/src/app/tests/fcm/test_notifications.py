"""Unit tests for FCM notification logic."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.fcm.notifications import (
    build_notification_content,
    build_notification_data,
    build_notification_title,
    build_zone_message,
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
SEND_EACH = "app.fcm.notifications.messaging.send_each"
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
        fire_centre_id=1,
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
        fire_centre_id=1,
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
        patch(SEND_EACH) as mock_send,
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
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=[]),
        patch(SEND_EACH) as mock_send,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_send.assert_not_called()


@pytest.mark.anyio
async def test_trigger_notifications_sends_messages():
    """Zones with advisories and subscribers triggers send_each with one Message per token."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label="K2-Kamloops Zone (Kamloops)", status="advisory"
    )
    tokens = ["token_a", "token_b"]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_EACH, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_send.assert_called_once()
        messages = mock_send.call_args[0][0]
        assert len(messages) == 2
        assert all(isinstance(m, messaging.Message) for m in messages)
        assert {m.token for m in messages} == set(tokens)
        assert all(m.notification.title == "Fire Behaviour Advisory, K2" for m in messages)
        assert all("K2-Kamloops Zone (Kamloops)" in m.notification.body for m in messages)


@pytest.mark.anyio
async def test_trigger_notifications_groups_zones_per_device():
    """A device subscribed to two advisory zones gets both messages in one send_each call."""
    session = AsyncMock()
    zone_a = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="1", placename_label="K5-Penticton Zone", status="advisory"
    )
    zone_b = ZoneAdvisoryStatus(
        advisory_shape_id=2, fire_centre_id=1, source_identifier="2", placename_label="K6-Merritt Zone", status="advisory"
    )
    shared_token = "shared_token"
    zone_a_only_token = "zone_a_token"
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone_a, zone_b]),
        patch(GET_TOKENS, side_effect=[[shared_token, zone_a_only_token], [shared_token]]),
        patch(SEND_EACH, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_send.assert_called_once()
        messages = mock_send.call_args[0][0]
        # shared_token gets zone_a + zone_b messages; zone_a_only_token gets zone_a only
        assert len(messages) == 3
        shared_msgs = [m for m in messages if m.token == shared_token]
        assert len(shared_msgs) == 2


@pytest.mark.anyio
async def test_trigger_notifications_batches_messages_over_limit():
    """Total messages over FCM_BATCH_SIZE are split into multiple send_each calls."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = [f"token_{i}" for i in range(501)]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_EACH, return_value=mock_response) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock),
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        assert mock_send.call_count == 2
        first_batch = mock_send.call_args_list[0][0][0]
        second_batch = mock_send.call_args_list[1][0][0]
        assert len(first_batch) == 500
        assert len(second_batch) == 1


@pytest.mark.anyio
async def test_trigger_notifications_calls_handle_response():
    """handle_fcm_response is called with the correct arguments after send."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = ["token_a"]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(SEND_EACH, return_value=mock_response),
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        mock_handle.assert_called_once_with(session, FOR_DATE, tokens, mock_response)


@pytest.mark.anyio
async def test_trigger_notifications_continues_on_batch_failure():
    """A FirebaseError on one batch does not abort subsequent batches."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label="Kamloops", status="advisory"
    )
    tokens = [f"token_{i}" for i in range(501)]
    mock_response = MagicMock(spec=messaging.BatchResponse)
    mock_response.failure_count = 0

    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS, return_value=tokens),
        patch(
            SEND_EACH,
            side_effect=[firebase_exceptions.UnavailableError("FCM error", None), mock_response],
        ) as mock_send,
        patch("app.fcm.notifications.handle_fcm_response", new_callable=AsyncMock) as mock_handle,
        patch(GET_VANCOUVER_NOW) as mock_now,
    ):
        mock_now.return_value.date.return_value = FOR_DATE
        await trigger_notifications(session, RunTypeEnum.forecast, RUN_GET_VANCOUVER_NOW, FOR_DATE)
        assert mock_send.call_count == 2
        mock_handle.assert_called_once()  # Only the second batch succeeded


@pytest.mark.anyio
async def test_trigger_notifications_skips_zone_with_missing_placename():
    """Zones with no placename_label are skipped — no tokens fetched, no notification sent."""
    session = AsyncMock()
    zone = ZoneAdvisoryStatus(
        advisory_shape_id=1, fire_centre_id=1, source_identifier="42", placename_label=None, status="advisory"
    )
    with (
        patch(GET_ZONES, return_value=[zone]),
        patch(GET_TOKENS) as mock_get_tokens,
        patch(SEND_EACH) as mock_send,
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
        await handle_fcm_response(session, date(2026, 4, 1), ["t1", "t2"], response)
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
            session, date(2026, 4, 1), ["token_good", "token_bad"], response
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
        await handle_fcm_response(session, date(2026, 4, 1), ["token_ok"], response)
        mock_update.assert_not_called()


@pytest.mark.anyio
async def test_handle_fcm_response_deduplicates_failed_tokens():
    """A token that fails for multiple zones (appears twice) is deactivated only once."""
    session = AsyncMock()
    resp_fail = MagicMock(
        success=False, exception=messaging.UnregisteredError("token expired", None)
    )
    response = MagicMock(spec=messaging.BatchResponse)
    response.failure_count = 2
    response.responses = [resp_fail, resp_fail]

    with patch(UPDATE_TOKENS, new_callable=AsyncMock) as mock_update:
        await handle_fcm_response(
            session, date(2026, 4, 1), ["token_bad", "token_bad"], response
        )
        called_tokens = mock_update.call_args[0][1]
        assert called_tokens.count("token_bad") == 1


ZONE = ZoneAdvisoryStatus(
    advisory_shape_id=1,
    fire_centre_id=7,
    source_identifier="42",
    placename_label="K2-Kamloops Zone (Kamloops)",
    status="advisory",
)
TOKEN = "device_token_abc"
MSG_DATE = date(2026, 4, 1)
FIXED_NOW = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
EXPECTED_APNS_EXPIRATION = str(int((FIXED_NOW + timedelta(days=2)).timestamp()))


def test_build_notification_data():
    data = build_notification_data(ZONE, MSG_DATE)
    assert data == {
        "advisory_date": "2026-04-01",
        "fire_centre_id": "7",
        "fire_zone_unit": "42",
    }


def test_build_zone_message_notification_content():
    msg = build_zone_message(MSG_DATE, ZONE, TOKEN)
    assert isinstance(msg, messaging.Message)
    assert msg.token == TOKEN
    assert msg.notification.title == "Fire Behaviour Advisory, K2"
    assert "K2-Kamloops Zone (Kamloops)" in msg.notification.body
    assert "Wed, April 1" in msg.notification.body
    assert msg.data == {
        "advisory_date": "2026-04-01",
        "fire_centre_id": "7",
        "fire_zone_unit": "42",
    }


def test_build_zone_message_platform_tags():
    with patch("app.fcm.notifications.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_NOW
        msg = build_zone_message(MSG_DATE, ZONE, TOKEN)

    assert msg.android.notification.tag == "advisory-42"
    assert msg.apns.payload.aps.thread_id == msg.android.notification.tag
    assert msg.android.ttl == timedelta(days=2)
    assert msg.apns.headers["apns-expiration"] == EXPECTED_APNS_EXPIRATION
