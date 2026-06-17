"""
Job for running SFMS daily actuals weather interpolation and FWI processing.

Usage:
    python -m app.jobs.sfms_daily_actuals "YYYY-MM-DD"
    python -m app.jobs.sfms_daily_actuals  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from aiohttp import ClientSession
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.run_type import RunType
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

from app.jobs.sfms_run_pipeline import (
    FWICalculationJob,
    RasterInterpolationJob,
    _missing_seed_keys,
    run_derived_fwi_calculations,
    run_fwi_calculations,
    run_fwi_interpolation,
    run_weather_interpolation,
)

logger = logging.getLogger(__name__)


def is_fwi_interpolation_day(dt: datetime) -> bool:
    """Return True if FWI indices should be re-interpolated from station observations.

    Re-interpolation resets the FWI grid from measured station values rather than
    calculating forward from yesterday's raster. This happens every Monday in
    April and May to align with the start of the fire season.
    """
    return dt.weekday() == 0 and dt.month in (4, 5)


async def run_sfms_daily_actuals(target_date: datetime) -> None:
    """Run SFMS daily weather interpolation and FWI updates for the given date."""
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    raster_addresser = SFMSNGRasterAddresser()

    # Create processor for target date (noon UTC hour 20)
    datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

    async with get_async_read_session_scope() as db_session:
        fuel_type_raster = await get_fuel_type_raster_by_year(db_session, datetime_to_process.year)
    if fuel_type_raster is None:
        raise RuntimeError(f"No fuel type raster found for {datetime_to_process.year}")
    fuel_raster_path = raster_addresser.gdal_path(fuel_type_raster.object_store_path)
    logger.info("Using reference raster: %s", fuel_raster_path)

    async with S3Client() as s3_client:
        # Fetch station observations from WF1
        async with ClientSession() as session:
            wfwx_api = WfwxApi(session)
            sfms_actuals = await wfwx_api.get_sfms_daily_actuals_all_stations(datetime_to_process)

        if not sfms_actuals:
            raise RuntimeError(f"No station observations found for {datetime_to_process}")

        async with get_async_write_session_scope() as session:
            station_codes = [actual.code for actual in sfms_actuals]
            sfms_run_id = await save_sfms_run(
                session,
                RunTypeEnum.actual,
                datetime_to_process.date(),
                get_utc_now(),
                station_codes,
            )

            await run_weather_interpolation(
                datetime_to_process,
                raster_addresser,
                s3_client,
                fuel_raster_path,
                sfms_actuals,
                sfms_run_id,
                session,
                RunType.ACTUAL,
            )

            if is_fwi_interpolation_day(datetime_to_process):
                await run_fwi_interpolation(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    fuel_raster_path,
                    sfms_actuals,
                    sfms_run_id,
                    session,
                    RunType.ACTUAL,
                )
                await run_derived_fwi_calculations(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    sfms_run_id,
                    session,
                    RunType.ACTUAL,
                )
            else:
                await run_fwi_calculations(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    sfms_run_id,
                    session,
                    RunType.ACTUAL,
                )

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
        logger.exception("An exception occurred while running SFMS daily actuals")
        chatops_message = "Encountered error running SFMS daily actuals"
        send_chatops_notification(chatops_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
