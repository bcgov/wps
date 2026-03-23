from sqlalchemy import Integer, cast, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.auto_spatial_advisory import Shape, ShapeType, ShapeTypeEnum
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


async def get_notification_settings_for_device(session: AsyncSession, device_id: str) -> list[int]:
    """Return the subscribed fire zone source identifiers for the given device_id."""
    result = await session.execute(
        select(cast(Shape.source_identifier, Integer))
        .join(
            NotificationSettings,
            NotificationSettings.fire_shape_source_id == Shape.source_identifier,
        )
        .join(DeviceToken, NotificationSettings.device_token_id == DeviceToken.id)
        .where(DeviceToken.device_id == device_id)
    )
    return list(result.scalars().all())


async def get_fire_zone_unit_shape_type_id(session: AsyncSession) -> int | None:
    return await session.scalar(
        select(ShapeType.id).where(ShapeType.name == ShapeTypeEnum.fire_zone_unit)
    )


async def _resolve_fire_zone_source_identifiers(
    session: AsyncSession, fire_zone_source_ids: list[int]
) -> list[int]:
    if not fire_zone_source_ids:
        return []

    fire_zone_unit_shape_type_id = await get_fire_zone_unit_shape_type_id(session)
    if fire_zone_unit_shape_type_id is None:
        return []

    requested_source_identifiers = [str(source_id) for source_id in fire_zone_source_ids]
    result = await session.execute(
        select(Shape.id, Shape.source_identifier).where(
            Shape.shape_type == fire_zone_unit_shape_type_id,
            Shape.source_identifier.in_(requested_source_identifiers),
        )
    )
    shape_ids_by_source_identifier = {
        int(source_identifier): shape_id for shape_id, source_identifier in result.all()
    }
    resolved_shape_ids = [
        shape_ids_by_source_identifier[source_id]
        for source_id in fire_zone_source_ids
        if source_id in shape_ids_by_source_identifier
    ]
    return list(dict.fromkeys(resolved_shape_ids))


async def upsert_notification_settings(
    session: AsyncSession, device_id: str, fire_zone_source_ids: list[int]
) -> None:
    """Replace device subscriptions using fire zone source identifiers from the API."""
    device_token = await get_device_by_device_id(session, device_id)
    if device_token is None:
        return

    await session.execute(
        delete(NotificationSettings).where(NotificationSettings.device_token_id == device_token.id)
    )

    for fire_zone_source_id in fire_zone_source_ids:
        session.add(
            NotificationSettings(
                device_token_id=device_token.id, fire_shape_source_id=fire_zone_source_id
            )
        )


async def get_device_tokens_for_zone(session: AsyncSession, fire_shape_source_id: int) -> list[str]:
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
