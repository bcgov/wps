import logging
from datetime import date, datetime, timedelta, timezone

from firebase_admin import exceptions as firebase_exceptions
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import ZoneAdvisoryStatus, get_zones_with_advisories
from wps_shared.db.crud.fcm import get_device_tokens_for_zone, update_device_tokens_are_active
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.utils.time import convert_to_sfms_timezone, get_vancouver_now

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


def build_fcm_message(
    for_date: date, zone_with_advisory: ZoneAdvisoryStatus, device_tokens: list[str]
):
    title = build_notification_title(zone_with_advisory)
    content = build_notification_content(zone_with_advisory, for_date)
    data = build_notification_data(zone_with_advisory, for_date)
    tag = f"advisory-{zone_with_advisory.source_identifier}"
    ttl = timedelta(days=2)
    apns_expiration = str(int((datetime.now(timezone.utc) + ttl).timestamp()))
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=content),
        android=messaging.AndroidConfig(
            ttl=ttl, notification=messaging.AndroidNotification(tag=tag), priority="high"
        ),
        apns=messaging.APNSConfig(
            headers={"apns-expiration": apns_expiration, "apns-priority": "10"},
            payload=messaging.APNSPayload(aps=messaging.Aps(thread_id=tag)),
        ),
        data=data,
        tokens=device_tokens,
    )

    return message


def should_send_notifications(
    completed_now: bool,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    vancouver_now: datetime,
    environment: str | None,
) -> bool:
    """Return whether an advisory run should send user notifications.

    Notifications are only sent when a run is completed for the first time and is today's
    forecast. In production, the run must have been created and processed during the same
    Vancouver morning. Other environments skip the morning restriction so notification delivery
    can be tested at any time.
    """
    if not completed_now or run_type == RunTypeEnum.actual or for_date != vancouver_now.date():
        return False

    if environment != "production":
        return True

    run_datetime_vancouver = convert_to_sfms_timezone(run_datetime)
    return (
        run_datetime_vancouver.date() == vancouver_now.date()
        and run_datetime_vancouver.hour < 12
        and vancouver_now.hour < 12
    )


async def trigger_notifications(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    *,
    completed_now: bool,
) -> None:
    vancouver_now = get_vancouver_now()
    environment = config.get("ENVIRONMENT")
    if not should_send_notifications(
        completed_now, run_type, run_datetime, for_date, vancouver_now, environment
    ):
        logger.info(
            "Skipping FCM notifications: eligibility criteria not met for run_type=%s "
            "run_datetime=%s for_date=%s completed_now=%s vancouver_now=%s environment=%s",
            run_type,
            run_datetime,
            for_date,
            completed_now,
            vancouver_now,
            environment,
        )
        return

    logger.info("Checking for warnings/advisories to send FCM notifications for")
    zones_with_advisories = await get_zones_with_advisories(
        session, run_type, run_datetime, for_date
    )
    logger.info(
        f"{len(zones_with_advisories)} have warnings/advisories, checking for devices to notify"
    )
    for zone_with_advisory in zones_with_advisories:
        if not zone_with_advisory.placename_label:
            logger.error(
                "Skipping FCM notification: missing placename_label for zone source_identifier=%s",
                zone_with_advisory.source_identifier,
            )
            continue
        device_tokens = await get_device_tokens_for_zone(
            session, zone_with_advisory.source_identifier
        )
        if len(device_tokens) == 0:
            logger.info(f"No devices subscribed to {zone_with_advisory.placename_label}")
            continue
        logger.info(
            f"{len(device_tokens)} are subscribed to {zone_with_advisory.placename_label} about to notify"
        )
        for i in range(0, len(device_tokens), FCM_BATCH_SIZE):
            batch = device_tokens[i : i + FCM_BATCH_SIZE]
            message = build_fcm_message(for_date, zone_with_advisory, batch)
            try:
                logger.info(f"Notifiying {len(batch)} devices")
                response = await messaging.send_each_for_multicast_async(message)
            except firebase_exceptions.FirebaseError:
                logger.exception(
                    "FCM send failed for zone=%s date=%s token_count=%d",
                    zone_with_advisory.placename_label,
                    for_date,
                    len(batch),
                )
                continue
            await handle_fcm_response(
                session, for_date, zone_with_advisory.placename_label, batch, response
            )


async def handle_fcm_response(
    session: AsyncSession,
    for_date: date,
    placename_label: str,
    device_tokens: list[str],
    response: messaging.BatchResponse,
):
    logger.info(
        f"Received FCM response with successful notifications sent: {response.success_count}"
    )
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
