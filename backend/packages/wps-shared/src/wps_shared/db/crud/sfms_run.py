"""CRUD operations for SFMS run log."""

import functools
import logging
from datetime import date, datetime
from typing import List

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.sfms_run import (
    SFMSRun,
    SFMSRunLog,
    SFMSRunLogJobName,
    SFMSRunLogStatus,
)
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


async def save_sfms_run_log(
    session: AsyncSession,
    job_name: str,
    status: SFMSRunLogStatus,
    sfms_run_id: int,
) -> int:
    """Insert an SFMSRunLog row and return its id.

    :param session: An async database session.
    :param record: The SFMSRunLog record to insert.
    :return: The id of the newly inserted row.
    """
    stmt = (
        insert(SFMSRunLog)
        .values(job_name=job_name, status=status, sfms_run_id=sfms_run_id)
        .returning(SFMSRunLog.id)
    )
    result = await session.execute(stmt)
    return result.scalar()


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
    sfms_run_id: int,
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
            log_id = await save_sfms_run_log(
                session, job_name, SFMSRunLogStatus.RUNNING, sfms_run_id
            )

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


async def save_sfms_run(
    session: AsyncSession,
    run_type: RunTypeEnum,
    target_date: date,
    run_datetime: datetime,
    stations: List[int],
) -> int:
    """Insert an SFMSRun row and return its id.

    :param session: An async database session.
    :param run_type: The run type, forecast or actual.
    :param target_date: The target date of the sfms run.
    :param run_date: The actual run date and time of the sfms run.
    :param stations: The list of stations used for the sfms run.
    :return: The id of the newly inserted row.
    """
    stmt = (
        insert(SFMSRun)
        .values(
            run_type=run_type,
            target_date=target_date,
            run_datetime=run_datetime,
            stations=stations,
        )
        .returning(SFMSRun.id)
    )
    result = await session.execute(stmt)
    return result.scalar()
