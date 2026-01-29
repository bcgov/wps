"""
Job for running SFMS daily actuals: temperature interpolation followed by
precipitation interpolation for the current date.

Usage:
    python -m app.jobs.sfms_daily_actuals "YYYY-MM-DD"
    python -m app.jobs.sfms_daily_actuals  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from app.jobs.temperature_interpolation_job import TemperatureInterpolationJob
from app.jobs.precipitation_interpolation_job import PrecipitationInterpolationJob
from wps_shared.db.crud.sfms_run_log import save_sfms_run_log, update_sfms_run_log
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.sfms_run_log import SFMSRunLog
from wps_shared.wps_logging import configure_logging
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)

JOB_NAME = "sfms_daily_actuals"


async def run_sfms_daily_actuals(target_date: datetime) -> None:
    """Run temperature then precipitation interpolation for the given date."""
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    async with get_async_write_session_scope() as session:
        log_record = SFMSRunLog(
            job_name=JOB_NAME,
            target_date=target_date.date(),
            started_at=get_utc_now(),
            status="running",
        )
        log_id = await save_sfms_run_log(session, log_record)

    try:
        temperature_job = TemperatureInterpolationJob()
        await temperature_job.run(target_date)

        precipitation_job = PrecipitationInterpolationJob()
        await precipitation_job.run(target_date)

        async with get_async_write_session_scope() as session:
            await update_sfms_run_log(session, log_id, status="success", completed_at=get_utc_now())

        logger.info("SFMS daily actuals completed successfully for %s", target_date.date())
    except Exception:
        async with get_async_write_session_scope() as session:
            await update_sfms_run_log(session, log_id, status="failed", completed_at=get_utc_now())
        raise


def main():
    """Main entry point for the job."""
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date in 'YYYY-MM-DD' format")
            sys.exit(1)
    else:
        target_date = get_utc_now()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_sfms_daily_actuals(target_date))
    except Exception as exception:
        logger.error("An exception occurred while running SFMS daily actuals", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
