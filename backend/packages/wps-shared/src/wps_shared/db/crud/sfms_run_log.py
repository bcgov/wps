"""CRUD operations for SFMS run log."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.sfms_run_log import SFMSRunLog


async def save_sfms_run_log(session: AsyncSession, record: SFMSRunLog) -> int:
    """Insert an SFMSRunLog row and return its id.

    :param session: An async database session.
    :param record: The SFMSRunLog record to insert.
    :return: The id of the newly inserted row.
    """
    session.add(record)
    await session.flush()
    return record.id


async def update_sfms_run_log(session: AsyncSession, log_id: int, status: str, completed_at: datetime):
    """Update status and completed_at for an existing SFMSRunLog row.

    :param session: An async database session.
    :param log_id: The id of the row to update.
    :param status: The new status value.
    :param completed_at: The completion timestamp.
    """
    record = await session.get(SFMSRunLog, log_id)
    record.status = status
    record.completed_at = completed_at
