from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.auto_spatial_advisory import Shape
from wps_shared.db.models.fcm import DeviceToken, NotificationSettings
from wps_shared.utils.time import get_utc_now


class DeviceTokenConflictError(Exception):
    """Raised when a device ID and token belong to different rows."""

    def __init__(self, device_id_row_id: int, token_row_id: int):
        self.device_id_row_id = device_id_row_id
        self.token_row_id = token_row_id
        super().__init__(
            f"Device registration conflict: device_id row {device_id_row_id} "
            f"differs from token row {token_row_id}"
        )


def save_device_token(session: AsyncSession, device_token: DeviceToken):
    """Add a new DeviceToken for tracking devices registered for push notifications.
    :param session: An async database session.
    :param device_token: The record to be saved.
    :type device_token: DeviceToken
    """
    session.add(device_token)


async def get_device_token_for_registration(
    session: AsyncSession, device_id: str, token: str
) -> DeviceToken | None:
    """Lock and return the row matching the device ID or token.

    Return None when neither value exists. Raise DeviceTokenConflictError when the values match two
    different rows.
    """
    statement = (
        select(DeviceToken)
        .where(or_(DeviceToken.device_id == device_id, DeviceToken.token == token))
        .order_by(DeviceToken.id)
        .with_for_update()
    )
    rows = list((await session.scalars(statement)).all())
    device_id_match = next((row for row in rows if row.device_id == device_id), None)
    token_match = next((row for row in rows if row.token == token), None)

    if (
        device_id_match is not None
        and token_match is not None
        and device_id_match.id != token_match.id
    ):
        raise DeviceTokenConflictError(device_id_match.id, token_match.id)

    return device_id_match or token_match


async def get_device_by_device_id(session: AsyncSession, device_id: str) -> DeviceToken | None:
    return await session.scalar(select(DeviceToken).where(DeviceToken.device_id == device_id))


async def get_active_device_by_device_id(
    session: AsyncSession, device_id: str, for_update: bool = False
) -> DeviceToken | None:
    """Return the active token row for a device.

    When for_update is True, lock the active token row until the transaction finishes so
    concurrent subscription replacements for the same device cannot interleave.
    """
    statement = select(DeviceToken).where(
        DeviceToken.device_id == device_id, DeviceToken.is_active.is_(True)
    )
    if for_update:
        statement = statement.with_for_update()
    return await session.scalar(statement)


async def get_device_by_token(session: AsyncSession, token: str) -> DeviceToken | None:
    return await session.scalar(select(DeviceToken).where(DeviceToken.token == token))


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
    if not tokens:
        return 0
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
        .where(DeviceToken.device_id == device_id, DeviceToken.is_active.is_(True))
    )
    return list(result.scalars().all())


async def upsert_notification_settings(
    session: AsyncSession, device_id: str, fire_zone_source_ids: list[str]
) -> bool:
    """Replace device subscriptions using fire zone source identifiers from the API.

    Returns False if the device_id is not found, True otherwise.
    """
    device_token = await get_active_device_by_device_id(session, device_id, for_update=True)
    if device_token is None:
        return False

    await session.execute(
        delete(NotificationSettings).where(NotificationSettings.device_token_id == device_token.id)
    )

    for fire_zone_source_id in set(fire_zone_source_ids):
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
        )
    )
    return list(result.scalars().all())
