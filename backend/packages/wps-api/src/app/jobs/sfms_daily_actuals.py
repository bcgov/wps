"""
Job for running SFMS daily actuals weather interpolation and FWI processing.

Usage:
    python -m app.jobs.sfms_daily_actuals "YYYY-MM-DD"
    python -m app.jobs.sfms_daily_actuals  # Uses current date
"""

import asyncio
from dataclasses import dataclass
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Awaitable, Callable

from aiohttp import ClientSession

from wps_sfms.interpolation.fields import (
    build_dc_field,
    build_dewpoint_field,
    build_dmc_field,
    build_ffmc_field,
    build_precipitation_field,
    build_temperature_field,
    build_wind_speed_field,
    build_wind_vector_field,
)
from wps_sfms.processors.fwi import DCCalculator, DMCCalculator, FFMCCalculator, FWIProcessor
from wps_sfms.processors.idw import Interpolator, RasterProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_shared.geospatial.cog import generate_web_optimized_cog
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run, track_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RasterJob:
    job_name: SFMSRunLogJobName
    output_key: str
    log_label: str
    processor: RasterProcessor
    cog_key: str | None = None
    cog_input_path: str | None = None


def is_fwi_interpolation_day(dt: datetime) -> bool:
    """Return True if FWI indices should be re-interpolated from station observations.

    Re-interpolation resets the FWI grid from measured station values rather than
    calculating forward from yesterday's raster. This happens every Monday in
    April and May to align with the start of the fire season.
    """
    return dt.weekday() == 0 and dt.month in (4, 5)


async def _run_tracked_job(
    job_name: SFMSRunLogJobName,
    sfms_run_id: int,
    session,
    action: Callable[[], Awaitable[object]],
):
    @track_sfms_run(job_name, sfms_run_id, session)
    async def _wrapped():
        return await action()

    return await _wrapped()


async def _process_raster_job(
    *,
    job_name: SFMSRunLogJobName,
    sfms_run_id: int,
    session,
    processor: RasterProcessor,
    s3_client: S3Client,
    fuel_raster_path: str,
    output_key: str,
    log_label: str,
    cog_key: str | None = None,
    cog_input_path: str | None = None,
) -> None:
    async def _run() -> None:
        s3_key = await processor.process(s3_client, fuel_raster_path, output_key)
        if cog_key is not None and cog_input_path is not None:
            generate_web_optimized_cog(input_path=cog_input_path, output_path=cog_key)
            logger.info("%s: %s (COG: %s)", log_label, s3_key, cog_key)
            return
        logger.info("%s: %s", log_label, s3_key)

    await _run_tracked_job(job_name, sfms_run_id, session, _run)


async def run_weather_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    sfms_actuals: list,
    sfms_run_id: int,
    session,
) -> None:
    """Interpolate weather rasters from station observations."""
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()
    temp_output_key = raster_addresser.get_actual_weather_key(
        datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP
    )
    temp_raster_path = raster_addresser.gdal_path(temp_output_key)
    jobs = [
        RasterJob(
            job_name=SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            output_key=temp_output_key,
            log_label="Temperature interpolation raster",
            processor=TemperatureInterpolator(
                mask_path, dem_path, build_temperature_field(sfms_actuals)
            ),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.RH_INTERPOLATION,
            output_key=raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.RH
            ),
            log_label="RH interpolation raster",
            processor=RHInterpolator(
                mask_path, dem_path, temp_raster_path, build_dewpoint_field(sfms_actuals)
            ),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            output_key=raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_SPEED
            ),
            log_label="Wind speed interpolation raster",
            processor=WindSpeedInterpolator(mask_path, build_wind_speed_field(sfms_actuals)),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            output_key=raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_DIRECTION
            ),
            log_label="Wind direction interpolation raster",
            processor=WindDirectionInterpolator(mask_path, build_wind_vector_field(sfms_actuals)),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            output_key=raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP
            ),
            log_label="Precip interpolation raster",
            processor=Interpolator(mask_path, build_precipitation_field(sfms_actuals)),
        ),
    ]

    for job in jobs:
        await _process_raster_job(
            job_name=job.job_name,
            sfms_run_id=sfms_run_id,
            session=session,
            processor=job.processor,
            s3_client=s3_client,
            fuel_raster_path=fuel_raster_path,
            output_key=job.output_key,
            log_label=job.log_label,
        )


async def run_fwi_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    sfms_actuals: list,
    sfms_run_id: int,
    session,
) -> None:
    """Re-interpolate FFMC, DMC, and DC from station observations."""
    logger.info(
        "Monday in %s — running FWI index interpolation", datetime_to_process.strftime("%B")
    )

    mask_path = raster_addresser.get_mask_key()
    ffmc_output_key = raster_addresser.get_actual_index_key(datetime_to_process, FWIParameter.FFMC)
    dmc_output_key = raster_addresser.get_actual_index_key(datetime_to_process, FWIParameter.DMC)
    dc_output_key = raster_addresser.get_actual_index_key(datetime_to_process, FWIParameter.DC)
    jobs = [
        RasterJob(
            job_name=SFMSRunLogJobName.FFMC_INTERPOLATION,
            output_key=ffmc_output_key,
            log_label=f"{SFMSRunLogJobName.FFMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_ffmc_field(sfms_actuals)),
            cog_key=raster_addresser.get_cog_key(ffmc_output_key),
            cog_input_path=raster_addresser.gdal_path(ffmc_output_key),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.DMC_INTERPOLATION,
            output_key=dmc_output_key,
            log_label=f"{SFMSRunLogJobName.DMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dmc_field(sfms_actuals)),
            cog_key=raster_addresser.get_cog_key(dmc_output_key),
            cog_input_path=raster_addresser.gdal_path(dmc_output_key),
        ),
        RasterJob(
            job_name=SFMSRunLogJobName.DC_INTERPOLATION,
            output_key=dc_output_key,
            log_label=f"{SFMSRunLogJobName.DC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dc_field(sfms_actuals)),
            cog_key=raster_addresser.get_cog_key(dc_output_key),
            cog_input_path=raster_addresser.gdal_path(dc_output_key),
        ),
    ]

    for job in jobs:
        await _process_raster_job(
            job_name=job.job_name,
            sfms_run_id=sfms_run_id,
            session=session,
            processor=job.processor,
            s3_client=s3_client,
            fuel_raster_path=fuel_raster_path,
            output_key=job.output_key,
            log_label=job.log_label,
            cog_key=job.cog_key,
            cog_input_path=job.cog_input_path,
        )


async def run_fwi_calculations(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
) -> None:
    """Calculate FFMC, DMC, and DC from interpolated weather and yesterday's actuals."""
    logger.info(
        "Calculating FWI from existing rasters for %s",
        datetime_to_process.date(),
    )

    fwi_processor = FWIProcessor(datetime_to_process)
    month = datetime_to_process.month

    fwi_calculations = [
        (SFMSRunLogJobName.FFMC_CALCULATION, FFMCCalculator()),
        (SFMSRunLogJobName.DMC_CALCULATION, DMCCalculator(month)),
        (SFMSRunLogJobName.DC_CALCULATION, DCCalculator(month)),
    ]

    for job_name, calculator in fwi_calculations:

        async def _run(_calculator=calculator) -> None:
            _fwi_inputs = raster_addresser.get_actual_fwi_inputs(
                datetime_to_process, _calculator.fwi_param
            )
            await fwi_processor.calculate_index(
                s3_client, multi_wps_dataset_context, _calculator, _fwi_inputs
            )

        await _run_tracked_job(job_name, sfms_run_id, session, _run)


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
                )
            else:
                await run_fwi_calculations(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    sfms_run_id,
                    session,
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
        logger.error("An exception occurred while running SFMS daily actuals", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
