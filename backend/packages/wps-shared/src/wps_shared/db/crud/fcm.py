from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.auto_spatial_advisory import Shape
from wps_shared.db.models.fcm import DeviceToken, NotificationSettings
from wps_shared.utils.time import get_utc_now


def save_device_token(session: AsyncSession, device_token: DeviceToken):
    """Add a new DeviceToken for tracking devices registered for push notifications.
    :param session: An async database session.
    :param device_token: The record to be saved.
    :type device_token: DeviceToken
    """
    session.add(device_token)


async def get_device_by_device_id(session: AsyncSession, device_id: str):
    return await session.scalar(select(DeviceToken).where(DeviceToken.device_id == device_id))


async def update_device_token_is_active(session: AsyncSession, token: str, is_active: bool) -> bool:
    device_token = await session.scalar(select(DeviceToken).where(DeviceToken.token == token))
    if not device_token:
        return False
    device_token.is_active = is_active
    device_token.updated_at = get_utc_now()
    return True


async def update_device_tokens_are_active(
    session: AsyncSession, tokens: list[str], is_active: bool
) -> int:
    stmt = (
        update(DeviceToken)
        .where(DeviceToken.token.in_(tokens))
        .values(
            is_active=is_active,
            updated_at=get_utc_now(),
        )
        # No need to synchronize the session: set-based UPDATE + no ORM objects loaded.
        .execution_options(synchronize_session=False)
    )
    result = await session.execute(stmt)
    return result.rowcount or 0


async def deactivate_device_tokens(session: AsyncSession, tokens: list[str]) -> int:
    if not tokens:
        return 0

    stmt = (
        update(DeviceToken)
        .where(DeviceToken.token.in_(tokens))
        .values(
            is_active=False,
            updated_at=get_utc_now(),
        )
        # No need to synchronize the session: set-based UPDATE + no ORM objects loaded.
        .execution_options(synchronize_session=False)
    )
    result = await session.execute(stmt)

    return result.rowcount or 0


async def get_notification_settings_for_device(session: AsyncSession, device_id: str) -> list[str]:
    """Return the subscribed fire zone source identifiers for the given device_id."""
    result = await session.execute(
        select(NotificationSettings.fire_shape_source_id)
        .join(DeviceToken, NotificationSettings.device_token_id == DeviceToken.id)
        .where(DeviceToken.device_id == device_id)
    )
    return list(result.scalars().all())


async def upsert_notification_settings(
    session: AsyncSession, device_id: str, fire_zone_source_ids: list[str]
) -> bool:
    """Replace device subscriptions using fire zone source identifiers from the API.

    Returns False if the device_id is not found, True otherwise.
    """
    device_token = await get_device_by_device_id(session, device_id)
    if device_token is None:
        return False

    await session.execute(
        delete(NotificationSettings).where(NotificationSettings.device_token_id == device_token.id)
    )

    for fire_zone_source_id in fire_zone_source_ids:
        session.add(
            NotificationSettings(
                device_token_id=device_token.id, fire_shape_source_id=fire_zone_source_id
            )
        )
    return True


async def get_device_tokens_for_zone(session: AsyncSession, fire_shape_source_id: str) -> list[str]:
    """Return active FCM tokens subscribed to the given fire_shape_source_id."""
    result = await session.execute(
        select(DeviceToken.token)
        .join(NotificationSettings, NotificationSettings.device_token_id == DeviceToken.id)
        .where(
            NotificationSettings.fire_shape_source_id == fire_shape_source_id,
            DeviceToken.is_active == True,
        )  # noqa: E712
    )
    return list(result.scalars().all())
