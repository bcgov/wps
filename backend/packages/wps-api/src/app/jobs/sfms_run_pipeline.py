"""Shared SFMS weather interpolation and FWI calculation pipeline."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Awaitable, Callable, Protocol, TypeVar

from botocore.exceptions import ClientError
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
from wps_sfms.processors.foliar_moisture_content import FoliarMoistureContentProcessor
from wps_sfms.processors.idw import Interpolator, RasterProcessor
from wps_sfms.processors.primary_fire_behaviour import PrimaryFireBehaviourProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.temporal_fuel import publish_temporal_fuel_raster
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_sfms.run_manifest import SFMSRunManifest
from wps_sfms.raster_inputs import FoliarMoistureContentInputs
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
    FBPParameter,
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SFMSStageNode(Protocol):
    """A stage node that records run inputs on entry and outputs on successful exit."""

    def on_enter(self, context: "SFMSRunContext") -> None: ...

    def on_exit(self, context: "SFMSRunContext", result: object | None) -> None: ...


@dataclass(frozen=True)
class RasterInterpolationJob:
    """One tracked interpolation job: the parameter it interpolates and where it is written."""

    job_name: SFMSRunLogJobName
    parameter: SFMSInterpolatedWeatherParameter | FWIParameter
    output_key: str
    log_label: str
    processor: RasterProcessor

    def on_enter(self, context: "SFMSRunContext") -> None:
        # The raster output is the only trace metadata; it is recorded on successful exit.
        pass

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        context.manifest.record_raster_output(self.parameter, self.output_key)


@dataclass(frozen=True)
class FWICalculationJob:
    job_name: SFMSRunLogJobName
    calculator: FWICalculator
    output_key: S3Key

    def on_enter(self, context: "SFMSRunContext") -> None:
        # The output key is the only trace metadata; it is recorded on successful exit.
        pass

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        context.manifest.record_raster_output(self.calculator.fwi_param, self.output_key)


@dataclass(frozen=True)
class ResolvedTemporalFuelRaster:
    """A date's temporal fuel raster, and the archived Julian rasters its grid was built from."""

    path: GDALPath
    julian_archive_keys: Mapping[str, S3Key]


@dataclass(frozen=True)
class WeatherInterpolationStage:
    station_codes: tuple[int, ...]
    fuel_raster_path: GDALPath
    static_rasters: Mapping[str, str]

    def on_enter(self, context: "SFMSRunContext") -> None:
        context.manifest.record_station_codes(self.station_codes)
        context.manifest.record_base_fuel_raster(self.fuel_raster_path)
        context.manifest.record_static_rasters(self.static_rasters)

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        # The child raster nodes record weather outputs individually.
        pass


@dataclass(frozen=True)
class FWISeedStage:
    seed_keys: Mapping[FWIParameter, str]

    def on_enter(self, context: "SFMSRunContext") -> None:
        context.manifest.record_seed_rasters(self.seed_keys)

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        # The calculation nodes record FWI outputs individually.
        pass


@dataclass(frozen=True)
class TemporalFuelStage:
    def on_enter(self, context: "SFMSRunContext") -> None:
        # The exact Julian inputs are returned by the resolver after they are read.
        pass

    def on_exit(self, context: "SFMSRunContext", result: object | None) -> None:
        if not isinstance(result, ResolvedTemporalFuelRaster):
            raise TypeError("Temporal fuel stage must return a ResolvedTemporalFuelRaster")
        context.manifest.record_temporal_fuel_raster(result.path, result.julian_archive_keys)


@dataclass(frozen=True)
class FoliarMoistureContentStage:
    fmc_inputs: FoliarMoistureContentInputs
    target_date: date

    def on_enter(self, context: "SFMSRunContext") -> None:
        context.manifest.record_fmc_static_inputs(self.fmc_inputs)

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        context.manifest.record_fmc_raster(self.fmc_inputs, self.target_date)


@dataclass(frozen=True)
class PrimaryFBPStage:
    percent_conifer_path: GDALPath
    static_rasters: Mapping[str, str]
    output_keys: Mapping[FBPParameter, S3Key]

    def on_enter(self, context: "SFMSRunContext") -> None:
        context.manifest.record_percent_conifer_raster(self.percent_conifer_path)
        context.manifest.record_static_rasters(self.static_rasters)

    def on_exit(self, context: "SFMSRunContext", _result: object | None) -> None:
        for parameter, output_key in self.output_keys.items():
            context.manifest.record_raster_output(parameter, output_key)


def get_fwi_seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    run_type: RunType = RunType.ACTUAL,
) -> dict[FWIParameter, S3Key]:
    """Return the previous-day FFMC/DMC/DC seed raster keys for a run type."""
    previous_date = datetime_to_process - timedelta(days=1)
    return {
        param: raster_addresser.get_index_key(previous_date, param, run_type)
        for param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC)
    }


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


@dataclass
class StageTrace:
    """Per-run nested trace of stage entry and successful exit events."""

    _stack: list[str] = field(default_factory=list, repr=False)
    _events: list[str] = field(default_factory=list, repr=False)

    @staticmethod
    def name_for(node: SFMSStageNode) -> str:
        job_name = getattr(node, "job_name", None)
        return getattr(job_name, "value", None) or type(node).__name__

    def enter(self, stage_name: str) -> None:
        self._events.append(f"{'  ' * len(self._stack)}ENTER {stage_name}")
        self._stack.append(stage_name)

    def assert_current(self, stage_name: str) -> None:
        if not self._stack or self._stack[-1] != stage_name:
            raise RuntimeError(f"Unbalanced stage exit: {stage_name}")

    def exit(self, stage_name: str) -> None:
        self.assert_current(stage_name)
        self._stack.pop()
        self._events.append(f"{'  ' * len(self._stack)}EXIT {stage_name}")

    def render(self) -> str:
        """Render the recorded stage lifecycle as an indented tree."""
        return "\n".join(self._events)


@dataclass(frozen=True)
class SFMSRunContext:
    """What every stage of one SFMS run for one date shares: the date and run type being
    processed, the manifest its inputs and outputs are traced in, the run its jobs are tracked
    against, and the clients they read and write with."""

    datetime_to_process: datetime
    run_type: RunType
    sfms_run_id: int
    manifest: SFMSRunManifest
    session: AsyncSession
    s3_client: S3Client
    raster_addresser: SFMSNGRasterAddresser
    stage_trace: StageTrace = field(default_factory=StageTrace, repr=False, compare=False)

    @classmethod
    def start(
        cls,
        datetime_to_process: datetime,
        run_type: RunType,
        sfms_run_id: int,
        run_datetime: datetime,
        session: AsyncSession,
        s3_client: S3Client,
        raster_addresser: SFMSNGRasterAddresser,
    ) -> "SFMSRunContext":
        """Start a run, creating the manifest its inputs and outputs will be traced in.

        ``run_datetime`` is when the run was saved, and is the same value its ``sfms_run`` row
        records, so a manifest and that row can be joined on it.
        """
        return cls(
            datetime_to_process=datetime_to_process,
            run_type=run_type,
            sfms_run_id=sfms_run_id,
            manifest=SFMSRunManifest(
                run_type=run_type,
                for_date=datetime_to_process.date(),
                run_datetime=run_datetime,
            ),
            session=session,
            s3_client=s3_client,
            raster_addresser=raster_addresser,
        )

    def __post_init__(self):
        # a manifest that describes another run's date or type could never be joined to this one
        assert self.manifest.run_type == self.run_type, "the manifest must describe this run type"
        assert self.manifest.for_date == self.datetime_to_process.date(), (
            "the manifest must describe this target date"
        )

    async def track(self, job_name: SFMSRunLogJobName, action: Callable[[], Awaitable[T]]) -> T:
        """Run ``action`` as a job of this run, logged under ``job_name``."""
        return await _run_tracked_job(job_name, self.sfms_run_id, self.session, action)

    def with_session(self, session: AsyncSession) -> "SFMSRunContext":
        """Return this run context using another session while preserving its manifest."""
        return SFMSRunContext(
            datetime_to_process=self.datetime_to_process,
            run_type=self.run_type,
            sfms_run_id=self.sfms_run_id,
            manifest=self.manifest,
            session=session,
            s3_client=self.s3_client,
            raster_addresser=self.raster_addresser,
            stage_trace=self.stage_trace,
        )

    def enter_node(self, node: SFMSStageNode, stage_name: str | None = None) -> None:
        """Invoke a stage node's input-recording hook with this run context."""
        stage_name = stage_name or self.stage_trace.name_for(node)
        self.stage_trace.enter(stage_name)
        node.on_enter(self)

    def exit_node(
        self, node: SFMSStageNode, result: object | None = None, stage_name: str | None = None
    ) -> None:
        """Invoke a stage node's output-recording hook after successful execution."""
        stage_name = stage_name or self.stage_trace.name_for(node)
        self.stage_trace.assert_current(stage_name)
        node.on_exit(self, result)
        self.stage_trace.exit(stage_name)

    async def run_stage(
        self,
        job_name: SFMSRunLogJobName,
        action: Callable[[], Awaitable[T]],
        trace_node: SFMSStageNode,
    ) -> T:
        """Track a stage and let its trace node record inputs on entry and outputs on success."""
        stage_name = job_name.value
        try:
            self.enter_node(trace_node, stage_name)
            result = await self.track(job_name, action)
            self.exit_node(trace_node, result, stage_name)
            return result
        except Exception as error:
            self.manifest.record_failure(stage_name, error)
            raise

    async def run_group(self, trace_node: SFMSStageNode, action: Callable[[], Awaitable[T]]) -> T:
        """Visit a multi-job stage around its successful execution."""
        stage_name = self.stage_trace.name_for(trace_node)
        try:
            self.enter_node(trace_node, stage_name)
            result = await action()
            self.exit_node(trace_node, result, stage_name)
            return result
        except Exception as error:
            self.manifest.record_failure(stage_name, error)
            raise

    async def write_manifest(self) -> None:
        """Upload the manifest tracing this run's inputs and outputs."""
        logger.info(
            "SFMS stage graph for %s %s:\n%s",
            self.run_type.value,
            self.datetime_to_process.date(),
            self.stage_trace.render() or "No stages recorded",
        )
        await self.manifest.write(self.s3_client)


async def run_fmc_calculations(contexts: list[SFMSRunContext], fuel_raster_path: GDALPath) -> None:
    """Calculate shared FMC rasters and trace the inputs/outputs on each date's run context."""
    if not contexts:
        return

    stage_name = "foliar_moisture_content"
    try:
        raster_addresser = contexts[0].raster_addresser
        fmc_inputs = raster_addresser.get_fmc_inputs(
            [context.datetime_to_process.date() for context in contexts], fuel_raster_path
        )
        trace_nodes = [
            FoliarMoistureContentStage(fmc_inputs, context.datetime_to_process.date())
            for context in contexts
        ]
        for context, node in zip(contexts, trace_nodes):
            context.enter_node(node, stage_name)

        await FoliarMoistureContentProcessor(raster_addresser).process(
            contexts[0].s3_client,
            multi_wps_dataset_context,
            fmc_inputs,
        )

        for context, node in zip(contexts, trace_nodes):
            context.exit_node(node, stage_name=stage_name)
    except Exception as error:
        for context in contexts:
            context.manifest.record_failure(stage_name, error)
        raise


async def write_failure_manifests(
    contexts: list[SFMSRunContext], stage: str, error: Exception
) -> None:
    """Best-effort persist failure manifests without masking the original stage exception."""
    for context in contexts:
        if context.manifest.status == "success":
            continue
        context.manifest.record_failure(stage, error)
        try:
            await context.write_manifest()
        except Exception:
            logger.exception(
                "Failed to write SFMS failure manifest for %s %s",
                context.run_type.value,
                context.datetime_to_process.date(),
            )


async def _process_raster_job(
    ctx: SFMSRunContext, job: RasterInterpolationJob, fuel_raster_path: str
) -> None:
    async def _run() -> None:
        s3_key = await job.processor.process(ctx.s3_client, fuel_raster_path, job.output_key)
        logger.info("%s: %s", job.log_label, s3_key)

    await ctx.run_stage(job.job_name, _run, job)


async def get_missing_fwi_seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    run_type: RunType = RunType.ACTUAL,
) -> list[str]:
    """Return any missing previous-day FFMC/DMC/DC seed rasters."""
    missing_keys = []
    for param, key in get_fwi_seed_keys(datetime_to_process, raster_addresser, run_type).items():
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
) -> ResolvedTemporalFuelRaster:
    """Return the temporal fuel raster for a date, creating a new version when needed.

    An existing raster is reused only when it was built from the same base fuel raster and the
    same green-up and grass curing Julian date rasters. The resolved raster carries the archived
    Julian raster keys its grid was built from, since the live Julian keys are replaced over time.
    """
    julian = await read_julian_rasters(s3_client, raster_addresser)
    # outside the date lock: concurrent runs would write identical bytes to the same keys
    await ensure_julian_archives(s3_client, julian)
    julian_archive_keys = {raster.name: raster.archive_key for raster in julian}

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
            return ResolvedTemporalFuelRaster(
                path=raster_addresser.gdal_path(existing.object_store_path),
                julian_archive_keys=julian_archive_keys,
            )
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
    return ResolvedTemporalFuelRaster(
        path=raster_addresser.gdal_path(output_key),
        julian_archive_keys=julian_archive_keys,
    )


async def run_temporal_fuel(run: SFMSRunContext, fuel_type_raster: FuelTypeRaster) -> GDALPath:
    """Resolve the date's temporal fuel raster as a tracked job of the SFMS run."""

    async def _resolve() -> ResolvedTemporalFuelRaster:
        return await resolve_temporal_fuel_raster(
            run.datetime_to_process.date(),
            fuel_type_raster,
            run.raster_addresser,
            run.s3_client,
        )

    resolved = await run.run_stage(SFMSRunLogJobName.TEMPORAL_FUEL, _resolve, TemporalFuelStage())
    return resolved.path


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
    slope_key = raster_addresser.get_slope_key()
    aspect_key = raster_addresser.get_aspect_key()
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
        raster_addresser.gdal_path(slope_key),
        raster_addresser.gdal_path(aspect_key),
    )
    processor = PrimaryFireBehaviourProcessor(ctx.datetime_to_process)

    async def _run_primary_fbp() -> None:
        await processor.process(ctx.s3_client, multi_wps_dataset_context, inputs)

    await ctx.run_stage(
        SFMSRunLogJobName.PRIMARY_FBP_CALCULATION,
        _run_primary_fbp,
        PrimaryFBPStage(
            percent_conifer_path=percent_conifer_path,
            static_rasters={"slope": slope_key, "aspect": aspect_key},
            output_keys=inputs.output_keys,
        ),
    )


async def run_weather_interpolation(
    ctx: SFMSRunContext, fuel_raster_path: str, station_weather: list
) -> None:
    """Interpolate weather rasters from station weather records."""
    raster_addresser = ctx.raster_addresser
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()
    trace = WeatherInterpolationStage(
        station_codes=tuple(weather.code for weather in station_weather),
        fuel_raster_path=fuel_raster_path,
        static_rasters={"dem": dem_path, "mask": mask_path},
    )

    def weather_key(param: SFMSInterpolatedWeatherParameter) -> str:
        return raster_addresser.get_weather_key(ctx.datetime_to_process, param, ctx.run_type)

    temp_output_key = weather_key(SFMSInterpolatedWeatherParameter.TEMP)
    temp_raster_path = raster_addresser.gdal_path(temp_output_key)
    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            parameter=SFMSInterpolatedWeatherParameter.TEMP,
            output_key=temp_output_key,
            log_label="Temperature interpolation raster",
            processor=TemperatureInterpolator(
                mask_path, dem_path, build_temperature_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.RH_INTERPOLATION,
            parameter=SFMSInterpolatedWeatherParameter.RH,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.RH),
            log_label="RH interpolation raster",
            processor=RHInterpolator(
                mask_path, dem_path, temp_raster_path, build_dewpoint_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            parameter=SFMSInterpolatedWeatherParameter.WIND_SPEED,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.WIND_SPEED),
            log_label="Wind speed interpolation raster",
            processor=WindSpeedInterpolator(mask_path, build_wind_speed_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            parameter=SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.WIND_DIRECTION),
            log_label="Wind direction interpolation raster",
            processor=WindDirectionInterpolator(
                mask_path, build_wind_vector_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            parameter=SFMSInterpolatedWeatherParameter.PRECIP,
            output_key=weather_key(SFMSInterpolatedWeatherParameter.PRECIP),
            log_label="Precip interpolation raster",
            processor=Interpolator(mask_path, build_precipitation_field(station_weather)),
        ),
    ]

    async def _run_jobs() -> None:
        for job in jobs:
            await _process_raster_job(ctx, job, fuel_raster_path)

    await ctx.run_group(trace, _run_jobs)


async def run_fwi_interpolation(
    ctx: SFMSRunContext, fuel_raster_path: str, station_weather: list
) -> None:
    """Re-interpolate FFMC, DMC, and DC from station weather records."""
    logger.info(
        "Monday in %s - running FWI index interpolation", ctx.datetime_to_process.strftime("%B")
    )

    mask_path = ctx.raster_addresser.get_mask_key()
    trace = WeatherInterpolationStage(
        station_codes=tuple(weather.code for weather in station_weather),
        fuel_raster_path=fuel_raster_path,
        static_rasters={"mask": mask_path},
    )

    def index_key(param: FWIParameter) -> str:
        return ctx.raster_addresser.get_index_key(ctx.datetime_to_process, param, ctx.run_type)

    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.FFMC_INTERPOLATION,
            parameter=FWIParameter.FFMC,
            output_key=index_key(FWIParameter.FFMC),
            log_label=f"{SFMSRunLogJobName.FFMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_ffmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DMC_INTERPOLATION,
            parameter=FWIParameter.DMC,
            output_key=index_key(FWIParameter.DMC),
            log_label=f"{SFMSRunLogJobName.DMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DC_INTERPOLATION,
            parameter=FWIParameter.DC,
            output_key=index_key(FWIParameter.DC),
            log_label=f"{SFMSRunLogJobName.DC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dc_field(station_weather)),
        ),
    ]

    async def _run_jobs() -> None:
        for job in jobs:
            await _process_raster_job(ctx, job, fuel_raster_path)

    await ctx.run_group(trace, _run_jobs)


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
    for calculator in calculators:
        fwi_inputs = ctx.raster_addresser.get_fwi_inputs(
            ctx.datetime_to_process,
            calculator.fwi_param,
            ctx.run_type,
            previous_base_run_type=previous_base_run_type,
        )
        job = FWICalculationJob(
            job_name=job_names_by_param[calculator.fwi_param],
            calculator=calculator,
            output_key=fwi_inputs.output_key,
        )

        async def _run(_calculator=calculator, _inputs=fwi_inputs) -> None:
            await fwi_processor.calculate_index(
                ctx.s3_client, multi_wps_dataset_context, _calculator, _inputs
            )

        await ctx.run_stage(job.job_name, _run, job)


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
            error = RuntimeError(message)
            ctx.manifest.record_failure("fwi_seed_check", error)
            raise error
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
    await ctx.run_group(
        FWISeedStage(
            get_fwi_seed_keys(ctx.datetime_to_process, ctx.raster_addresser, seed_run_type)
        ),
        lambda: _run_fwi_calculation_jobs(
            ctx, full_fwi_calculators, previous_base_run_type=previous_base_run_type
        ),
    )
    return True


async def run_derived_fwi_calculations(ctx: SFMSRunContext) -> None:
    """Calculate ISI, BUI, and FWI from same-day weather and interpolated base indices."""
    derived_fwi_calculators = (ISICalculator(), BUICalculator(), FWIFinalCalculator())
    await _run_fwi_calculation_jobs(ctx, derived_fwi_calculators)
