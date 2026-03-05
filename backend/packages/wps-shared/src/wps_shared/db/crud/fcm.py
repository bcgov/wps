from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.fcm import DeviceToken
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
