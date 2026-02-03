"""CRUD operations for SFMS run log."""

import functools
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.sfms_run_log import (
    SFMSRunLog,
    SFMSRunLogJobName,
    SFMSRunLogStatus,
    SFMSStations,
)
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


async def save_sfms_run_log(session: AsyncSession, record: SFMSRunLog) -> int:
    """Insert an SFMSRunLog row and return its id.

    :param session: An async database session.
    :param record: The SFMSRunLog record to insert.
    :return: The id of the newly inserted row.
    """
    session.add(record)
    await session.flush()
    return record.id


async def update_sfms_run_log(
    session: AsyncSession, log_id: int, status: SFMSRunLogStatus, completed_at: datetime
):
    """Update status and completed_at for an existing SFMSRunLog row.

    :param session: An async database session.
    :param log_id: The id of the row to update.
    :param status: The new status value.
    :param completed_at: The completion timestamp.
    """
    record = await session.get(SFMSRunLog, log_id)
    record.status = status
    record.completed_at = completed_at


def track_sfms_run(
    job_name: SFMSRunLogJobName,
    datetime_to_process: datetime,
    sfms_stations_id: int,
    session: AsyncSession,
):
    """Decorator that logs an sfms_run_log entry around an async function.

    :param job_name: Name to record in the run log.
    :param datetime_to_process: The datetime being processed.
    :param session: An async database session for run-log operations.

    Usage::

        @track_sfms_run(SFMSRunLogJobName.TEMPERATURE_INTERPOLATION, datetime_to_process, session)
        async def run_temperature() -> None:
            ...
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            log_record = SFMSRunLog(
                job_name=job_name,
                target_date=datetime_to_process.date(),
                started_at=get_utc_now(),
                status=SFMSRunLogStatus.RUNNING,
                sfms_stations_id=sfms_stations_id,
            )
            log_id = await save_sfms_run_log(session, log_record)

            try:
                # Calculate execution time
                start_exec = get_utc_now()
                result = await fn(*args, **kwargs)
                execution_time = get_utc_now() - start_exec
                hours, remainder = divmod(execution_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                logger.info(
                    f"{job_name.value} interpolation completed successfully -- "
                    "time elapsed %d hours, %d minutes, %.2f seconds",
                    hours,
                    minutes,
                    seconds,
                )
                await update_sfms_run_log(
                    session, log_id, status=SFMSRunLogStatus.SUCCESS, completed_at=get_utc_now()
                )
                return result
            except Exception:
                await update_sfms_run_log(
                    session, log_id, status=SFMSRunLogStatus.FAILED, completed_at=get_utc_now()
                )
                raise

        return wrapper

    return decorator


async def save_sfms_stations(session: AsyncSession, record: SFMSStations) -> int:
    """Insert an SFMSStations row and return its id.

    :param session: An async database session.
    :param record: The SFMSStations record to insert.
    :return: The id of the newly inserted row.
    """
    session.add(record)
    await session.flush()
    return record.id
