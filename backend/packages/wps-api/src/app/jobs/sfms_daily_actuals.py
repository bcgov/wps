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
from wps_shared.db.crud.sfms_run_log import track_sfms_run
from wps_shared.wps_logging import configure_logging
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


@track_sfms_run("temperature_interpolation")
async def run_temperature_interpolation(target_date: datetime) -> None:
    """Run temperature interpolation for the given date."""
    temperature_job = TemperatureInterpolationJob()
    await temperature_job.run(target_date)


@track_sfms_run("precipitation_interpolation")
async def run_precipitation_interpolation(target_date: datetime) -> None:
    """Run precipitation interpolation for the given date."""
    precipitation_job = PrecipitationInterpolationJob()
    await precipitation_job.run(target_date)


async def run_sfms_daily_actuals(target_date: datetime) -> None:
    """Run temperature then precipitation interpolation for the given date."""
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    await run_temperature_interpolation(target_date)
    await run_precipitation_interpolation(target_date)

    logger.info("SFMS daily actuals completed successfully for %s", target_date.date())


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
