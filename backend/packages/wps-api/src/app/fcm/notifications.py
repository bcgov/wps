import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from firebase_admin import exceptions as firebase_exceptions
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus, get_zones_with_advisories
from wps_shared.db.crud.fcm import get_device_tokens_for_zone, update_device_tokens_are_active
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.utils.time import get_vancouver_now

logger = logging.getLogger(__name__)

FCM_BATCH_SIZE = 500


def build_notification_content(zone_with_advisory: ZoneAdvisoryStatus, for_date: date):
    return f"{for_date.strftime('%a, %B %-d')} - An advisory has been issued for {zone_with_advisory.placename_label}"


def build_notification_title(zone_with_advisory: ZoneAdvisoryStatus):
    zone = zone_with_advisory.placename_label.split("-")[0]
    return f"Fire Behaviour Advisory, {zone}"


def build_notification_data(zone_with_advisory: ZoneAdvisoryStatus, for_date: date) -> dict:
    return {
        "advisory_date": for_date.isoformat(),
        "fire_centre_id": str(zone_with_advisory.fire_centre_id),
        "fire_zone_unit": str(zone_with_advisory.source_identifier),
    }


def build_zone_message(for_date: date, zone: ZoneAdvisoryStatus, token: str) -> messaging.Message:
    """Build a single-token FCM Message for one zone advisory."""
    title = build_notification_title(zone)
    body = build_notification_content(zone, for_date)
    data = build_notification_data(zone, for_date)
    tag = f"advisory-{zone.source_identifier}"
    ttl = timedelta(days=2)
    apns_expiration = str(int((datetime.now(timezone.utc) + ttl).timestamp()))
    return messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        android=messaging.AndroidConfig(
            ttl=ttl, notification=messaging.AndroidNotification(tag=tag)
        ),
        apns=messaging.APNSConfig(
            headers={"apns-expiration": apns_expiration},
            payload=messaging.APNSPayload(aps=messaging.Aps(thread_id=tag)),
        ),
        data=data,
        token=token,
    )


async def trigger_notifications(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> None:
    if run_type == RunTypeEnum.actual:
        return

    vancouver_now = get_vancouver_now()

    if for_date != vancouver_now.date():
        logger.info("Skipping FCM notifications: for_date=%s is not today", for_date)
        return

    if config.get("ENVIRONMENT") == "production":
        if vancouver_now.hour >= 12:
            logger.info(
                "Skipping FCM notifications: current Vancouver time hour=%d is at or after noon",
                vancouver_now.hour,
            )
            return

    logger.info("Checking for warnings/advisories to send FCM notifications for")
    zones_with_advisories = await get_zones_with_advisories(
        session, run_type, run_datetime, for_date
    )
    logger.info(
        f"{len(zones_with_advisories)} have warnings/advisories, checking for devices to notify"
    )

    # Build per-device map: token → list of advisory zones the device is subscribed to.
    device_zones: dict[str, list[ZoneAdvisoryStatus]] = {}
    for zone_with_advisory in zones_with_advisories:
        if not zone_with_advisory.placename_label:
            logger.error(
                "Skipping FCM notification: missing placename_label for zone source_identifier=%s",
                zone_with_advisory.source_identifier,
            )
            continue
        tokens = await get_device_tokens_for_zone(session, zone_with_advisory.source_identifier)
        if not tokens:
            logger.info(f"No devices subscribed to {zone_with_advisory.placename_label}")
            continue
        logger.info(f"{len(tokens)} are subscribed to {zone_with_advisory.placename_label}")
        for token in tokens:
            device_zones.setdefault(token, []).append(zone_with_advisory)

    if not device_zones:
        return

    # Flatten to parallel (token, message) lists grouped by device so that all of a
    # device's zone notifications are dispatched in the same send_each call. This
    # prevents APNs from dropping earlier notifications when multiple zone advisories
    # arrive on a device in rapid succession.
    all_tokens: list[str] = []
    all_messages: list[messaging.Message] = []
    for token, zones in device_zones.items():
        for zone in zones:
            all_tokens.append(token)
            all_messages.append(build_zone_message(for_date, zone, token))

    logger.info(f"Notifying {len(device_zones)} devices ({len(all_messages)} total messages)")

    for i in range(0, len(all_messages), FCM_BATCH_SIZE):
        batch_messages = all_messages[i : i + FCM_BATCH_SIZE]
        batch_tokens = all_tokens[i : i + FCM_BATCH_SIZE]
        try:
            # messaging.send_each is a synchronous blocking call
            response = await asyncio.to_thread(messaging.send_each, batch_messages)
        except firebase_exceptions.FirebaseError:
            logger.exception(
                "FCM send failed for date=%s message_count=%d",
                for_date,
                len(batch_messages),
            )
            continue
        await handle_fcm_response(session, for_date, batch_tokens, response)


async def handle_fcm_response(
    session: AsyncSession,
    for_date: date,
    device_tokens: list[str],
    response: messaging.BatchResponse,
):
    logger.info(
        f"Received FCM response with successful notifications sent: {response.success_count}"
    )
    # Only deactivate permanently invalid tokens (UnregisteredError — token is no longer registered).
    # Transient failures (quota, server errors) are not deactivated; the token remains valid.
    # Deactivated tokens are re-activated when the app re-registers on open.
    # Use a set to deduplicate: a token subscribed to multiple zones may appear more than once.
    permanently_failed = list({
        device_tokens[idx]
        for idx, resp in enumerate(response.responses)
        if not resp.success and isinstance(resp.exception, messaging.UnregisteredError)
    })
    transient_failed_count = response.failure_count - len(permanently_failed)

    if response.failure_count > 0:
        logger.warning(
            "FCM send for date=%s: %d permanent failures, %d transient failures out of %d messages",
            for_date,
            len(permanently_failed),
            transient_failed_count,
            len(device_tokens),
        )

    if permanently_failed:
        await update_device_tokens_are_active(session, permanently_failed, False)
