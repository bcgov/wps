import logging
from datetime import date, datetime

from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus, get_zones_with_advisories
from wps_shared.db.crud.fcm import get_device_tokens_for_zone, update_device_tokens_are_active
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum

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
    if run_type == RunTypeEnum.forecast:
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
            response = messaging.send_each_for_multicast(message)
        except Exception:
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
    failed_tokens = []
    successful_tokens = []
    for idx, resp in enumerate(response.responses):
        if resp.success:
            successful_tokens.append(device_tokens[idx])
        else:
            failed_tokens.append(device_tokens[idx])

    if failed_tokens:
        logger.warning(
            "Failed issuing notification for zone: %s and date: %s to devices: %s",
            placename_label,
            for_date,
            failed_tokens,
        )
    if successful_tokens:
        await update_device_tokens_are_active(session, successful_tokens, True)
    if failed_tokens:
        await update_device_tokens_are_active(session, failed_tokens, False)
