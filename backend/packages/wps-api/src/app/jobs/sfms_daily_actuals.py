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

from aiohttp import ClientSession

from wps_sfms.interpolation.source import (
    StationDCSource,
    StationDewPointSource,
    StationDMCSource,
    StationFFMCSource,
    StationPrecipitationSource,
    StationTemperatureSource,
)
from wps_sfms.processors.idw import IDWInterpolationProcessor
from wps_sfms.processors.relative_humidity import RHInterpolationProcessor
from wps_sfms.processors.temperature import TemperatureInterpolationProcessor
from wps_shared.db.crud.sfms_run import save_sfms_run, track_sfms_run
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.fuel_raster import find_latest_version
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


async def run_sfms_daily_actuals(target_date: datetime) -> None:
    """Run temperature then precipitation interpolation for the given date."""
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    raster_addresser = RasterKeyAddresser()

    # Create processor for target date (noon UTC hour 20)
    datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

    async with S3Client() as s3_client:
        # Use a reference raster for grid properties
        # We'll use the fuel raster which defines the SFMS grid

        latest_version = await find_latest_version(
            s3_client, raster_addresser, datetime_to_process, 1
        )
        fuel_raster_key = raster_addresser.get_fuel_raster_key(target_date, version=latest_version)
        fuel_raster_path = raster_addresser.s3_prefix + "/" + fuel_raster_key
        logger.info("Using reference raster: %s", fuel_raster_path)

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

            @track_sfms_run(
                SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
                sfms_run_id,
                session,
            )
            async def run_temperature_interpolation() -> None:
                temperature_processor = TemperatureInterpolationProcessor(
                    datetime_to_process, raster_addresser
                )
                temp_s3_key = await temperature_processor.process(
                    s3_client,
                    fuel_raster_path,
                    StationTemperatureSource(sfms_actuals),
                )
                logger.info("Temperature interpolation raster: %s", temp_s3_key)

            @track_sfms_run(
                SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
                sfms_run_id,
                session,
            )
            async def run_precipitation_interpolation() -> None:
                processor = IDWInterpolationProcessor(datetime_to_process, raster_addresser)
                precip_s3_key = await processor.process(
                    s3_client,
                    fuel_raster_path,
                    sfms_actuals,
                    StationPrecipitationSource(),
                )
                logger.info("Precip interpolation raster: %s", precip_s3_key)

            @track_sfms_run(SFMSRunLogJobName.RH_INTERPOLATION, sfms_run_id, session)
            async def run_rh_interpolation() -> None:
                rh_processor = RHInterpolationProcessor(datetime_to_process, raster_addresser)
                rh_s3_key = await rh_processor.process(
                    s3_client,
                    fuel_raster_path,
                    StationDewPointSource(sfms_actuals),
                )
                logger.info("RH interpolation raster: %s", rh_s3_key)

            await run_temperature_interpolation()
            await run_rh_interpolation()
            await run_precipitation_interpolation()

            # Interpolate FWI indices (FFMC, DMC, DC) on the first Monday of April and May
            is_monday = datetime_to_process.weekday() == 0
            is_first_week = datetime_to_process.day <= 7
            is_april_or_may = datetime_to_process.month in (4, 5)
            if is_monday and is_first_week and is_april_or_may:
                logger.info(
                    "First Monday of %s — running FWI index interpolation",
                    datetime_to_process.strftime("%B"),
                )

                fwi_sources = [
                    (SFMSRunLogJobName.FFMC_INTERPOLATION, StationFFMCSource()),
                    (SFMSRunLogJobName.DMC_INTERPOLATION, StationDMCSource()),
                    (SFMSRunLogJobName.DC_INTERPOLATION, StationDCSource()),
                ]

                for job_name, source in fwi_sources:

                    @track_sfms_run(job_name, sfms_run_id, session)
                    async def run_fwi_interpolation() -> None:
                        processor = IDWInterpolationProcessor(datetime_to_process, raster_addresser)
                        s3_key = await processor.process(
                            s3_client,
                            fuel_raster_path,
                            sfms_actuals,
                            source,
                        )
                        logger.info("%s interpolation raster: %s", job_name.value, s3_key)

                    await run_fwi_interpolation()

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
