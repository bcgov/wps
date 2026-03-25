import asyncio
import logging
from datetime import date, datetime

from firebase_admin import exceptions as firebase_exceptions
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus, get_zones_with_advisories
from wps_shared.db.crud.fcm import get_device_tokens_for_zone, update_device_tokens_are_active
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.utils.time import get_vancouver_now

logger = logging.getLogger(__name__)


def build_notification_content(zone_with_advisory: ZoneAdvisoryStatus, for_date: date):
    return f"{for_date.strftime('%a, %B %-d')} - An advisory has been issued for {zone_with_advisory.placename_label}"


def build_notification_title(zone_with_advisory: ZoneAdvisoryStatus):
    label = zone_with_advisory.placename_label or "Unknown Zone"
    zone = label.split("-")[0]
    return f"Behaviour Advisory, {zone}"


async def trigger_notifications(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> None:
    if run_type == RunTypeEnum.actual:
        return

    if for_date != get_vancouver_now().date():
        logger.info("Skipping FCM notifications: for_date=%s is not today", for_date)
        return

    logger.info("Checking for warnings/advisories to send FCM notifications for")
    zones_with_advisories = await get_zones_with_advisories(
        session, run_type, run_datetime, for_date
    )
    for zone_with_advisory in zones_with_advisories:
        device_tokens = await get_device_tokens_for_zone(
            session, zone_with_advisory.source_identifier
        )
        if len(device_tokens) == 0:
            continue
        title = build_notification_title(zone_with_advisory)
        content = build_notification_content(zone_with_advisory, for_date)
        tag = f"advisory-{zone_with_advisory.source_identifier}"
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=content),
            android=messaging.AndroidConfig(notification=messaging.AndroidNotification(tag=tag)),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(thread_id=tag))
            ),
            tokens=device_tokens,
        )
        try:
            # messaging.send_each_for_multicast is a synchronous blocking call
            response = await asyncio.to_thread(messaging.send_each_for_multicast, message)
        except firebase_exceptions.FirebaseError:
            logger.exception(
                "FCM send failed for zone=%s date=%s token_count=%d",
                zone_with_advisory.placename_label,
                for_date,
                len(device_tokens),
            )
            continue
        await handle_fcm_response(
            session, for_date, zone_with_advisory.placename_label, device_tokens, response
        )


async def handle_fcm_response(
    session,
    for_date,
    placename_label: str,
    device_tokens: list[str],
    response: messaging.BatchResponse,
):
    # Only deactivate permanently invalid tokens (UnregisteredError — token is no longer registered).
    # Transient failures (quota, server errors) are not deactivated; the token remains valid.
    # Deactivated tokens are re-activated when the app re-registers on open.
    permanently_failed = [
        device_tokens[idx]
        for idx, resp in enumerate(response.responses)
        if not resp.success and isinstance(resp.exception, messaging.UnregisteredError)
    ]
    transient_failed_count = response.failure_count - len(permanently_failed)

    if response.failure_count > 0:
        logger.warning(
            "FCM send for zone=%s date=%s: %d permanent failures, %d transient failures out of %d tokens",
            placename_label,
            for_date,
            len(permanently_failed),
            transient_failed_count,
            len(device_tokens),
        )

    if permanently_failed:
        await update_device_tokens_are_active(session, permanently_failed, False)
