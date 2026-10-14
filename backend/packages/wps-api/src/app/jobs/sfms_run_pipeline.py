"""Shared SFMS weather interpolation and FWI calculation pipeline."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Awaitable, Callable, TypeVar

from aiohttp import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from wps_sfms.interpolation.field import (
    build_dc_field,
    build_dewpoint_field,
    build_dmc_field,
    build_ffmc_field,
    build_precipitation_field,
    build_temperature_field,
    build_wind_speed_field,
    build_wind_vector_field,
)
from wps_sfms.julian_rasters import ensure_julian_archives, read_julian_rasters
from wps_sfms.processors.fwi import (
    BUICalculator,
    DCCalculator,
    DMCCalculator,
    FFMCCalculator,
    FWICalculator,
    FWIFinalCalculator,
    FWIProcessor,
    ISICalculator,
)
from wps_sfms.processors.idw import Interpolator, RasterProcessor
from wps_sfms.processors.primary_fire_behaviour import PrimaryFireBehaviourProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.temporal_fuel import publish_temporal_fuel_raster
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.db.crud.fuel_layer import (
    get_latest_temporal_fuel_raster_version,
    get_matching_temporal_fuel_raster,
    lock_temporal_fuel_raster_date,
)
from wps_shared.db.crud.sfms_run import track_sfms_run
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    GDALPath,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RasterInterpolationJob:
    job_name: SFMSRunLogJobName
    output_key: str
    log_label: str
    processor: RasterProcessor


@dataclass(frozen=True)
class FWICalculationJob:
    job_name: SFMSRunLogJobName
    calculator: FWICalculator


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


@dataclass(frozen=True)
class SFMSRunContext:
    """What every stage of one SFMS run for one date shares: the date and run type being
    processed, the run its jobs are tracked against, and the clients they read and write with."""

    datetime_to_process: datetime
    run_type: RunType
    sfms_run_id: int
    session: AsyncSession
    s3_client: S3Client
    raster_addresser: SFMSNGRasterAddresser

    async def track(self, job_name: SFMSRunLogJobName, action: Callable[[], Awaitable[T]]) -> T:
        """Run ``action`` as a job of this run, logged under ``job_name``."""
        return await _run_tracked_job(job_name, self.sfms_run_id, self.session, action)


async def _process_raster_job(
    ctx: SFMSRunContext, job: RasterInterpolationJob, fuel_raster_path: str
) -> None:
    async def _run() -> None:
        s3_key = await job.processor.process(ctx.s3_client, fuel_raster_path, job.output_key)
        logger.info("%s: %s", job.log_label, s3_key)

    await ctx.track(job.job_name, _run)


async def get_missing_fwi_seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    run_type: RunType = RunType.ACTUAL,
) -> list[str]:
    """Return any missing previous-day FFMC/DMC/DC seed rasters."""
    previous_date = datetime_to_process - timedelta(days=1)
    missing_keys = []
    for param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC):
        key = raster_addresser.get_index_key(previous_date, param, run_type)
        if not await s3_client.all_objects_exist(key):
            missing_keys.append(f"{param.value}={key}")

    return missing_keys


async def _stored_raster_matches(s3_client: S3Client, existing: TemporalFuelRaster) -> bool:
    """Return whether the stored raster still exists and matches its recorded content hash."""
    try:
        await s3_client.get_fuel_raster(existing.object_store_path, existing.content_hash)
    except ValueError:
        logger.warning(
            "Stored temporal fuel raster no longer matches its recorded hash: %s",
            existing.object_store_path,
        )
        return False
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
            raise
        logger.warning("Stored temporal fuel raster is missing: %s", existing.object_store_path)
        return False
    return True


async def resolve_temporal_fuel_raster(
    target_date: date,
    fuel_type_raster: FuelTypeRaster,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
) -> GDALPath:
    """Return the temporal fuel raster for a date, creating a new version when needed.

    An existing raster is reused only when it was built from the same base fuel raster and the
    same green-up and grass curing Julian date rasters.
    """
    julian = await read_julian_rasters(s3_client, raster_addresser)
    # outside the date lock: concurrent runs would write identical bytes to the same keys
    await ensure_julian_archives(s3_client, julian)

    async with get_async_write_session_scope() as session:
        # held until commit so concurrent runs for the same date reuse rather than collide
        await lock_temporal_fuel_raster_date(session, target_date)
        existing = await get_matching_temporal_fuel_raster(
            session, target_date, fuel_type_raster.id, **julian.hash_columns()
        )
        if existing is not None and await _stored_raster_matches(s3_client, existing):
            logger.info(
                "Reusing temporal fuel raster for %s: %s", target_date, existing.object_store_path
            )
            return raster_addresser.gdal_path(existing.object_store_path)
        # a grid is fully determined by its inputs, so a missing or altered one is rebuilt as the
        # next version, which the reuse query then prefers

        version = await get_latest_temporal_fuel_raster_version(session, target_date) + 1
        output_key = raster_addresser.get_temporal_fuel_key(target_date, version)
        logger.info(
            "Generating temporal fuel raster for %s, version %s, base raster %s: %s",
            target_date,
            version,
            fuel_type_raster.id,
            output_key,
        )
        with julian.as_datasets() as julian_datasets:
            content_hash = await publish_temporal_fuel_raster(
                s3_client,
                target_date,
                base_fuel_key=raster_addresser.gdal_path(fuel_type_raster.object_store_path),
                output_key=output_key,
                julian=julian_datasets,
            )
        session.add(
            TemporalFuelRaster(
                fuel_type_raster_id=fuel_type_raster.id,
                for_date=target_date,
                version=version,
                object_store_path=output_key,
                content_hash=content_hash,
                **julian.hash_columns(),
                **julian.archive_path_columns(),
                create_timestamp=get_utc_now(),
            )
        )
    return raster_addresser.gdal_path(output_key)


async def run_temporal_fuel(
    datetime_to_process: datetime,
    fuel_type_raster: FuelTypeRaster,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
) -> GDALPath:
    """Resolve the date's temporal fuel raster as a tracked job of the SFMS run."""

    async def _resolve() -> GDALPath:
        return await resolve_temporal_fuel_raster(
            datetime_to_process.date(), fuel_type_raster, raster_addresser, s3_client
        )

    return await _run_tracked_job(SFMSRunLogJobName.TEMPORAL_FUEL, sfms_run_id, session, _resolve)


async def _resolve_percent_conifer_path(
    fuel_raster_year: int,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
) -> GDALPath:
    """Resolve the percent-conifer raster matching the selected fuel-grid year."""
    key = raster_addresser.get_percent_conifer_key(fuel_raster_year)
    if await s3_client.object_exists(key):
        logger.info("Using percent-conifer raster: %s", key)
        return raster_addresser.gdal_path(key)

    raise RuntimeError(
        f"No percent-conifer raster found for fuel-grid year {fuel_raster_year}: {key}"
    )


async def _resolve_percent_dead_conifer_path(
    fuel_raster_year: int,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
) -> GDALPath:
    """Resolve the percent-dead-conifer raster matching the selected fuel-grid year."""
    key = raster_addresser.get_percent_dead_conifer_key(fuel_raster_year)
    if await s3_client.object_exists(key):
        logger.info("Using percent-dead-conifer raster: %s", key)
        return raster_addresser.gdal_path(key)

    raise RuntimeError(
        f"No percent-dead-conifer raster found for fuel-grid year {fuel_raster_year}: {key}"
    )


async def run_fbp_calculations(
    ctx: SFMSRunContext, fuel_raster_path: GDALPath, fuel_raster_year: int
) -> None:
    """Calculate and publish the same-day primary FBP products."""
    raster_addresser = ctx.raster_addresser
    percent_conifer_path = await _resolve_percent_conifer_path(
        fuel_raster_year, raster_addresser, ctx.s3_client
    )
    inputs = raster_addresser.get_primary_fire_behaviour_inputs(
        ctx.datetime_to_process,
        ctx.run_type,
        fuel_raster_path,
        percent_conifer_path,
        raster_addresser.gdal_path(
            raster_addresser.get_weather_key(
                ctx.datetime_to_process,
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
                ctx.run_type,
            )
        ),
        raster_addresser.gdal_path(
            raster_addresser.get_weather_key(
                ctx.datetime_to_process,
                SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
                ctx.run_type,
            )
        ),
        raster_addresser.gdal_path(raster_addresser.get_fmc_key(ctx.datetime_to_process.date())),
        raster_addresser.gdal_path(raster_addresser.get_slope_key()),
        raster_addresser.gdal_path(raster_addresser.get_aspect_key()),
    )
    processor = PrimaryFireBehaviourProcessor(ctx.datetime_to_process)

    async def _run_primary_fbp() -> None:
        await processor.process(ctx.s3_client, multi_wps_dataset_context, inputs)

    await ctx.track(SFMSRunLogJobName.PRIMARY_FBP_CALCULATION, _run_primary_fbp)


async def run_weather_interpolation(
    ctx: SFMSRunContext, fuel_raster_path: str, station_weather: list
) -> None:
    """Interpolate weather rasters from station weather records."""
    raster_addresser = ctx.raster_addresser
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()

    def weather_key(param: SFMSInterpolatedWeatherParameter) -> str:
        return raster_addresser.get_weather_key(ctx.datetime_to_process, param, ctx.run_type)

    temp_output_key = weather_key(SFMSInterpolatedWeatherParameter.TEMP)
    temp_raster_path = raster_addresser.gdal_path(temp_output_key)
    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            output_key=temp_output_key,
            log_label="Temperature interpolation raster",
            processor=TemperatureInterpolator(
                mask_path, dem_path, build_temperature_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.RH_INTERPOLATION,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.RH),
            log_label="RH interpolation raster",
            processor=RHInterpolator(
                mask_path, dem_path, temp_raster_path, build_dewpoint_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.WIND_SPEED),
            log_label="Wind speed interpolation raster",
            processor=WindSpeedInterpolator(mask_path, build_wind_speed_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.WIND_DIRECTION),
            log_label="Wind direction interpolation raster",
            processor=WindDirectionInterpolator(
                mask_path, build_wind_vector_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.PRECIP),
            log_label="Precip interpolation raster",
            processor=Interpolator(mask_path, build_precipitation_field(station_weather)),
        ),
    ]

    for job in jobs:
        await _process_raster_job(ctx, job, fuel_raster_path)


async def run_fwi_interpolation(
    ctx: SFMSRunContext, fuel_raster_path: str, station_weather: list
) -> None:
    """Re-interpolate FFMC, DMC, and DC from station weather records."""
    logger.info(
        "Monday in %s - running FWI index interpolation", ctx.datetime_to_process.strftime("%B")
    )

    mask_path = ctx.raster_addresser.get_mask_key()

    def index_key(param: FWIParameter) -> str:
        return ctx.raster_addresser.get_index_key(ctx.datetime_to_process, param, ctx.run_type)

    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.FFMC_INTERPOLATION,
            output_key=index_key(FWIParameter.FFMC),
            log_label=f"{SFMSRunLogJobName.FFMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_ffmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DMC_INTERPOLATION,
            output_key=index_key(FWIParameter.DMC),
            log_label=f"{SFMSRunLogJobName.DMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DC_INTERPOLATION,
            output_key=index_key(FWIParameter.DC),
            log_label=f"{SFMSRunLogJobName.DC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dc_field(station_weather)),
        ),
    ]

    for job in jobs:
        await _process_raster_job(ctx, job, fuel_raster_path)


async def _run_fwi_calculation_jobs(
    ctx: SFMSRunContext,
    calculators: tuple[FWICalculator, ...],
    previous_base_run_type: RunType | None = None,
) -> None:
    """Run the provided FWI calculator jobs in order."""
    logger.info(
        "Calculating %s FWI from existing rasters for %s",
        ctx.run_type.value,
        ctx.datetime_to_process.date(),
    )

    fwi_processor = FWIProcessor(ctx.datetime_to_process)

    job_names_by_param = {
        FWIParameter.FFMC: SFMSRunLogJobName.FFMC_CALCULATION,
        FWIParameter.DMC: SFMSRunLogJobName.DMC_CALCULATION,
        FWIParameter.DC: SFMSRunLogJobName.DC_CALCULATION,
        FWIParameter.ISI: SFMSRunLogJobName.ISI_CALCULATION,
        FWIParameter.BUI: SFMSRunLogJobName.BUI_CALCULATION,
        FWIParameter.FWI: SFMSRunLogJobName.FWI_CALCULATION,
    }
    jobs = [
        FWICalculationJob(
            job_name=job_names_by_param[calculator.fwi_param],
            calculator=calculator,
        )
        for calculator in calculators
    ]

    for job in jobs:

        async def _run(_calculator=job.calculator) -> None:
            _fwi_inputs = ctx.raster_addresser.get_fwi_inputs(
                ctx.datetime_to_process,
                _calculator.fwi_param,
                ctx.run_type,
                previous_base_run_type=previous_base_run_type,
            )
            await fwi_processor.calculate_index(
                ctx.s3_client, multi_wps_dataset_context, _calculator, _fwi_inputs
            )

        await ctx.track(job.job_name, _run)


async def run_fwi_calculations(
    ctx: SFMSRunContext,
    previous_base_run_type: RunType | None = None,
    raise_on_missing_seed_keys: bool = False,
) -> bool:
    """Calculate the full FWI chain from weather and previous-day seeds."""
    month = ctx.datetime_to_process.month
    seed_run_type = previous_base_run_type or ctx.run_type
    missing_previous_keys = await get_missing_fwi_seed_keys(
        ctx.datetime_to_process,
        ctx.raster_addresser,
        ctx.s3_client,
        seed_run_type,
    )
    if missing_previous_keys:
        previous_date = ctx.datetime_to_process - timedelta(days=1)
        message = (
            f"Missing previous-day {seed_run_type.value} index rasters for "
            f"{previous_date.date()}: {', '.join(missing_previous_keys)}"
        )
        if raise_on_missing_seed_keys:
            raise RuntimeError(message)
        logger.warning(
            "Skipping FWI calculations for %s because %s",
            ctx.datetime_to_process.date(),
            message,
        )
        return False

    full_fwi_calculators = (
        FFMCCalculator(),
        DMCCalculator(month),
        DCCalculator(month),
        ISICalculator(),
        BUICalculator(),
        FWIFinalCalculator(),
    )
    await _run_fwi_calculation_jobs(
        ctx, full_fwi_calculators, previous_base_run_type=previous_base_run_type
    )
    return True


async def run_derived_fwi_calculations(ctx: SFMSRunContext) -> None:
    """Calculate ISI, BUI, and FWI from same-day weather and interpolated base indices."""
    derived_fwi_calculators = (ISICalculator(), BUICalculator(), FWIFinalCalculator())
    await _run_fwi_calculation_jobs(ctx, derived_fwi_calculators)
