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
from datetime import UTC, datetime, timedelta

from aiohttp import ClientSession
from wps_sfms.fbp_step import calculate_primary_fbp
from wps_sfms.fmc_step import calculate_fmc
from wps_sfms.fwi_step import calculate_fwi, interpolate_fwi
from wps_sfms.run_context import SFMSRunContext
from wps_sfms.temporal_fuel_step import resolve_temporal_fuel
from wps_sfms.weather_step import interpolate_weather
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.run_type import RunType
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import assert_all_utc, get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi


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
    assert_all_utc(target_date)
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    raster_addresser = SFMSNGRasterAddresser()

    # Create processor for target date (noon UTC hour 20)
    datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

    async with get_async_read_session_scope() as db_session:
        fuel_type_raster = await get_fuel_type_raster_by_year(db_session, datetime_to_process.year)
    if fuel_type_raster is None:
        raise RuntimeError(f"No fuel type raster found for {datetime_to_process.year}")
    logger.info("Using reference raster: %s", fuel_type_raster.object_store_path)

    async with S3Client() as s3_client:
        # Fetch station observations from WF1
        async with ClientSession() as session:
            wfwx_api = WfwxApi(session)
            sfms_actuals = await wfwx_api.get_sfms_daily_weather_all_stations(datetime_to_process)

        if not sfms_actuals:
            raise RuntimeError(f"No station observations found for {datetime_to_process}")

        station_codes = [actual.code for actual in sfms_actuals]
        saved_run_datetime = get_utc_now()
        # committed before any job runs, so every run log row and manifest can be joined to it
        async with get_async_write_session_scope() as session:
            sfms_run_id = await save_sfms_run(
                session,
                RunTypeEnum.actual,
                datetime_to_process.date(),
                saved_run_datetime,
                station_codes,
            )

        ctx = SFMSRunContext.start(
            datetime_to_process=datetime_to_process,
            run_type=RunType.ACTUAL,
            sfms_run_id=sfms_run_id,
            run_datetime=saved_run_datetime,
            s3_client=s3_client,
            raster_addresser=raster_addresser,
            fuel_type_raster=fuel_type_raster,
            seed_actual_date=(datetime_to_process - timedelta(days=1)).date(),
            station_codes=station_codes,
        )
        try:
            fmc_key = await calculate_fmc(ctx)
            weather_keys = await interpolate_weather(ctx, sfms_actuals)
            if is_fwi_interpolation_day(datetime_to_process):
                fwi_keys = await interpolate_fwi(ctx, sfms_actuals, weather_keys)
            else:
                fwi_keys = await calculate_fwi(ctx, weather_keys)
            # None when the run had no previous-day seeds to calculate FWI from
            if fwi_keys is not None:
                temporal_fuel_path = await resolve_temporal_fuel(ctx)
                await calculate_primary_fbp(
                    ctx, temporal_fuel_path, fmc_key, weather_keys, fwi_keys
                )
            await ctx.write_manifest()
        except Exception as error:
            await ctx.write_manifest(error, step="daily_actuals")
            raise

    logger.info("SFMS daily actuals completed successfully for %s", target_date.date())


def main():
    """Main entry point for the job."""
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=UTC)
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
