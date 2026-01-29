"""CRUD operations for SFMS run log."""

import functools
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.sfms_run_log import SFMSRunLog
from wps_shared.utils.time import get_utc_now


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


def track_sfms_run(job_name: str, session: AsyncSession):
    """Decorator that logs an sfms_run_log entry around an async function.

    :param job_name: Name to record in the run log.
    :param session: An async database session for run-log operations.

    Usage::

        @track_sfms_run("temperature_interpolation", session)
        async def run_temperature(target_date: datetime) -> None:
            ...
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(target_date: datetime, *args, **kwargs):
            log_record = SFMSRunLog(
                job_name=job_name,
                target_date=target_date.date(),
                started_at=get_utc_now(),
                status="running",
            )
            log_id = await save_sfms_run_log(session, log_record)

            try:
                result = await fn(target_date, *args, **kwargs)
                await update_sfms_run_log(session, log_id, status="success", completed_at=get_utc_now())
                return result
            except Exception:
                await update_sfms_run_log(session, log_id, status="failed", completed_at=get_utc_now())
                raise

        return wrapper

    return decorator
