import logging
from datetime import date, datetime

from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.auto_spatial_advisory import get_zones_with_advisories
from wps_shared.db.crud.fcm import get_device_tokens_for_zone, update_device_tokens_are_active
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum

logger = logging.getLogger(__name__)


def build_notification_content(placename_label, for_date: date):
    return f"{for_date.isoformat()} - An advisory has been issued for {placename_label}"


async def trigger_notifications(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> None:
    if run_type == RunTypeEnum.forecast:
        return

    zones_with_advisories = await get_zones_with_advisories(
        session, run_type, run_datetime, for_date
    )
    for (
        _,
        source_identifier,
        placename_label,
        _,
    ) in zones_with_advisories:
        # TODO: this function should look up source_identifier
        device_tokens = await get_device_tokens_for_zone(session, source_identifier)
        if len(device_tokens) > 0:
            content = build_notification_content(placename_label, for_date)
            message = messaging.MulticastMessage(
                notification=messaging.Notification(body=content),
                tokens=device_tokens,
            )
            response = messaging.send_each_for_multicast(message)
            if response.failure_count > 0:
                responses = response.responses
                failed_tokens = []
                successful_tokens = []
                for idx, resp in enumerate(responses):
                    if resp.success:
                        successful_tokens.append(device_tokens[idx])
                    else:
                        # The order of responses corresponds to the order of the registration tokens.
                        failed_tokens.append(device_tokens[idx])

                logger.warning(
                    f"Failed sending notification for zone: {placename_label} and date: {for_date} to devices: {failed_tokens}"
                )
                updated_devices = await update_device_tokens_are_active(
                    session, successful_tokens, True
                )
                logger.info(f"Updated {updated_devices} as active")
