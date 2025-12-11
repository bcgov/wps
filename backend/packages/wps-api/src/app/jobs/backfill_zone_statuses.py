import asyncio
import logging
import os
import sys

from sqlalchemy import select
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunParameters
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.run_type import RunType
from wps_shared.wps_logging import configure_logging

from app.auto_spatial_advisory.process_zone_status import process_zone_statuses

logger = logging.getLogger(__name__)


async def backfill_all_zone_statuses():
    """Backfill advisory zone statuses for all existing complete runs."""
    logger.info("Starting backfill of advisory zone statuses for all complete runs.")
    async with get_async_write_session_scope() as session:
        # get all complete run_parameters
        stmt = select(RunParameters).where(RunParameters.complete == True)
        runs = await session.execute(stmt)

        for run in runs.scalars():
            await process_zone_statuses(
                RunType(run.run_type),
                run.run_datetime,
                run.for_date,
            )

    logger.info("Backfill of advisory zone statuses completed.")


def main():
    """Kicks off backfilling advisory zone statuses for all complete runs."""
    try:
        logger.debug("Begin backfilling advisory zone statuses.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(backfill_all_zone_statuses())

        sys.exit(os.EX_OK)
    except Exception as exception:
        logger.error(
            "An error occurred while backfilling advisory zone statuses.", exc_info=exception
        )
        rc_message = ":scream: Encountered an error while backfilling advisory zone statuses."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
