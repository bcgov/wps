"""Shared SFMS weather interpolation and FWI calculation pipeline."""

import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import ClassVar, Protocol, TypeVar

from botocore.exceptions import ClientError
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
from wps_sfms.processors.foliar_moisture_content import FoliarMoistureContentProcessor
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
from wps_sfms.raster_inputs import FWIInputs, PrimaryFireBehaviourInputs
from wps_sfms.run_manifest import SFMSRunManifest
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.db.crud.fuel_layer import (
    get_latest_temporal_fuel_raster_version,
    get_matching_temporal_fuel_raster,
    lock_temporal_fuel_raster_date,
)
from wps_shared.chatops_notification import send_chatops_notification
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
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)

T = TypeVar("T")
StageOutput = TypeVar("StageOutput", covariant=True)

WeatherKeys = Mapping[SFMSInterpolatedWeatherParameter, S3Key]
"""The object store keys of the weather rasters a run interpolated, by parameter."""

FWIKeys = Mapping[FWIParameter, S3Key]
"""The object store keys of FWI index rasters, by parameter."""


class SFMSStage(Protocol[StageOutput]):
    """A stage of an SFMS run.

    Running a stage records its inputs, runs its child stages and/or its own tracked work, then
    records its outputs, so the manifest is written in the order the run did things. A stage takes
    the keys of the rasters it reads from the stages that wrote them, and returns the keys of the
    rasters it writes for the stages that read them, so the dependencies between stages are in
    their signatures.
    """

    async def run(self, context: "SFMSRunContext") -> StageOutput: ...


@dataclass(frozen=True)
class RasterInterpolationJob(SFMSStage[S3Key]):
    """One tracked interpolation job: the parameter it interpolates and where it is written."""

    job_name: SFMSRunLogJobName
    parameter: SFMSInterpolatedWeatherParameter | FWIParameter
    output_key: S3Key
    log_label: str
    processor: RasterProcessor

    async def run(self, context: "SFMSRunContext") -> S3Key:
        async def _interpolate() -> None:
            s3_key = await self.processor.process(
                context.s3_client, context.base_fuel_raster_path, self.output_key
            )
            logger.info("%s: %s", self.log_label, s3_key)

        await context.track(self.job_name, _interpolate)
        context.manifest.record_raster_output(self.parameter, self.output_key)
        return self.output_key


@dataclass(frozen=True)
class FWICalculationJob(SFMSStage[S3Key]):
    """One tracked FWI index calculation for the run's date.

    ``index_keys`` are the keys of the index rasters it reads: the previous day's value for FFMC,
    DMC and DC, and the same day's FFMC for ISI, DMC and DC for BUI, and ISI and BUI for FWI.
    """

    JOB_NAMES: ClassVar[Mapping[FWIParameter, SFMSRunLogJobName]] = {
        FWIParameter.FFMC: SFMSRunLogJobName.FFMC_CALCULATION,
        FWIParameter.DMC: SFMSRunLogJobName.DMC_CALCULATION,
        FWIParameter.DC: SFMSRunLogJobName.DC_CALCULATION,
        FWIParameter.ISI: SFMSRunLogJobName.ISI_CALCULATION,
        FWIParameter.BUI: SFMSRunLogJobName.BUI_CALCULATION,
        FWIParameter.FWI: SFMSRunLogJobName.FWI_CALCULATION,
    }

    calculator: FWICalculator
    weather_keys: WeatherKeys
    index_keys: FWIKeys

    async def run(self, context: "SFMSRunContext") -> S3Key:
        fwi_param = self.calculator.fwi_param

        async def _calculate() -> FWIInputs:
            inputs = context.raster_addresser.get_fwi_inputs(
                context.datetime_to_process,
                fwi_param,
                context.run_type,
                self.weather_keys,
                self.index_keys,
            )
            await FWIProcessor(context.datetime_to_process).calculate_index(
                context.s3_client, multi_wps_dataset_context, self.calculator, inputs
            )
            return inputs

        inputs = await context.track(self.JOB_NAMES[fwi_param], _calculate)
        context.manifest.record_raster_output(fwi_param, inputs.output_key)
        return inputs.output_key


@dataclass(frozen=True)
class FoliarMoistureContentStage(SFMSStage[S3Key]):
    """Ensures the FMC raster for the run's date, from static rasters on the base fuel grid."""

    async def run(self, context: "SFMSRunContext") -> S3Key:
        target_date = context.datetime_to_process.date()
        fmc_inputs = context.raster_addresser.get_fmc_inputs(
            [target_date], context.base_fuel_raster_path
        )
        context.manifest.record_fmc_static_inputs(fmc_inputs)
        # ponytail: each forecast date reopens the static rasters; batch dates in one processor
        # call if FMC time matters
        await context.track(
            SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT,
            lambda: FoliarMoistureContentProcessor(context.raster_addresser).process(
                context.s3_client, multi_wps_dataset_context, fmc_inputs
            ),
        )
        context.manifest.record_fmc_raster(fmc_inputs, target_date)
        return fmc_inputs.output_keys[target_date]


@dataclass(frozen=True)
class WeatherInterpolationStage(SFMSStage[WeatherKeys]):
    """Interpolates the run's weather rasters from its station weather."""

    station_weather: list

    async def run(self, context: "SFMSRunContext") -> WeatherKeys:
        raster_addresser = context.raster_addresser
        mask_path = raster_addresser.get_mask_key()
        dem_path = raster_addresser.get_dem_key()
        context.manifest.record_static_rasters({"dem": dem_path, "mask": mask_path})
        weather_keys = {}
        for job in self._jobs(context, mask_path, dem_path):
            weather_keys[job.parameter] = await job.run(context)
        return weather_keys

    def _jobs(
        self, context: "SFMSRunContext", mask_path: GDALPath, dem_path: GDALPath
    ) -> list[RasterInterpolationJob]:
        raster_addresser = context.raster_addresser
        station_weather = self.station_weather

        def weather_key(param: SFMSInterpolatedWeatherParameter) -> str:
            return raster_addresser.get_weather_key(
                context.datetime_to_process, param, context.run_type
            )

        temp_output_key = weather_key(SFMSInterpolatedWeatherParameter.TEMP)
        temp_raster_path = raster_addresser.gdal_path(temp_output_key)
        return [
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


@dataclass(frozen=True)
class FWIInterpolationStage(SFMSStage[FWIKeys]):
    """Resets FFMC, DMC and DC from station weather, then derives ISI, BUI and FWI from them.

    Runs on April and May Mondays in place of calculating forward from previous-day seeds.
    """

    station_weather: list
    weather_keys: WeatherKeys

    async def run(self, context: "SFMSRunContext") -> FWIKeys:
        logger.info(
            "Monday in %s - running FWI index interpolation",
            context.datetime_to_process.strftime("%B"),
        )
        mask_path = context.raster_addresser.get_mask_key()
        context.manifest.record_static_rasters({"mask": mask_path})
        ffmc_job, dmc_job, dc_job = self._interpolation_jobs(context, mask_path)
        ffmc_key = await ffmc_job.run(context)
        dmc_key = await dmc_job.run(context)
        dc_key = await dc_job.run(context)
        isi_key = await FWICalculationJob(
            ISICalculator(), self.weather_keys, {FWIParameter.FFMC: ffmc_key}
        ).run(context)
        bui_key = await FWICalculationJob(
            BUICalculator(), self.weather_keys, {FWIParameter.DMC: dmc_key, FWIParameter.DC: dc_key}
        ).run(context)
        fwi_key = await FWICalculationJob(
            FWIFinalCalculator(),
            self.weather_keys,
            {FWIParameter.ISI: isi_key, FWIParameter.BUI: bui_key},
        ).run(context)
        return {
            FWIParameter.FFMC: ffmc_key,
            FWIParameter.DMC: dmc_key,
            FWIParameter.DC: dc_key,
            FWIParameter.ISI: isi_key,
            FWIParameter.BUI: bui_key,
            FWIParameter.FWI: fwi_key,
        }

    def _interpolation_jobs(
        self, context: "SFMSRunContext", mask_path: GDALPath
    ) -> list[RasterInterpolationJob]:
        fields = {
            FWIParameter.FFMC: (SFMSRunLogJobName.FFMC_INTERPOLATION, build_ffmc_field),
            FWIParameter.DMC: (SFMSRunLogJobName.DMC_INTERPOLATION, build_dmc_field),
            FWIParameter.DC: (SFMSRunLogJobName.DC_INTERPOLATION, build_dc_field),
        }
        return [
            RasterInterpolationJob(
                job_name=job_name,
                parameter=param,
                output_key=context.raster_addresser.get_index_key(
                    context.datetime_to_process, param, context.run_type
                ),
                log_label=f"{job_name.value} raster",
                processor=Interpolator(mask_path, build_field(self.station_weather)),
            )
            for param, (job_name, build_field) in fields.items()
        ]


@dataclass(frozen=True)
class FWICalculationStage(SFMSStage[FWIKeys | None]):
    """Calculates the full FWI chain forward from the previous day's FFMC, DMC and DC.

    The run seeds from the actual rasters when the previous day is the run's
    ``seed_actual_date``, and from the previous day's forecast otherwise: an actual run and the
    first forecast date seed from actuals, later forecast dates from the forecast before them.

    Missing seeds are recorded as a failure, and the stage skips FWI and returns None: a run can
    legitimately start without seeds (season start, backfills) and still produces weather.
    """

    weather_keys: WeatherKeys

    @staticmethod
    def seed_run_type(context: "SFMSRunContext") -> RunType:
        """The run type of the previous-day rasters this run calculates forward from."""
        previous_date = (context.datetime_to_process - timedelta(days=1)).date()
        if previous_date == context.seed_actual_date:
            return RunType.ACTUAL
        return RunType.FORECAST

    @staticmethod
    def seed_keys(
        datetime_to_process: datetime,
        raster_addresser: SFMSNGRasterAddresser,
        seed_run_type: RunType,
    ) -> FWIKeys:
        """The previous-day FFMC, DMC and DC raster keys of the seed run type."""
        previous_date = datetime_to_process - timedelta(days=1)
        return {
            param: raster_addresser.get_index_key(previous_date, param, seed_run_type)
            for param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC)
        }

    @staticmethod
    async def missing_seed_keys(
        datetime_to_process: datetime,
        raster_addresser: SFMSNGRasterAddresser,
        s3_client: S3Client,
        seed_run_type: RunType,
    ) -> list[str]:
        """Any previous-day FFMC, DMC and DC rasters of the seed run type that don't exist."""
        missing_keys = []
        seed_keys = FWICalculationStage.seed_keys(
            datetime_to_process, raster_addresser, seed_run_type
        )
        for param, key in seed_keys.items():
            if not await s3_client.all_objects_exist(key):
                missing_keys.append(f"{param.value}={key}")
        return missing_keys

    async def run(self, context: "SFMSRunContext") -> FWIKeys | None:
        seed_run_type = self.seed_run_type(context)
        missing_previous_keys = await self.missing_seed_keys(
            context.datetime_to_process,
            context.raster_addresser,
            context.s3_client,
            seed_run_type,
        )
        if missing_previous_keys:
            previous_date = context.datetime_to_process - timedelta(days=1)
            message = (
                f"Missing previous-day {seed_run_type.value} index rasters for "
                f"{previous_date.date()}: {', '.join(missing_previous_keys)}"
            )
            # recorded so a run without FWI or FBP isn't reported as a success
            context.manifest.record_failure("fwi_seed_check", RuntimeError(message))
            logger.warning(
                "Skipping FWI calculations for %s because %s",
                context.datetime_to_process.date(),
                message,
            )
            return None

        seed_keys = self.seed_keys(
            context.datetime_to_process, context.raster_addresser, seed_run_type
        )
        context.manifest.record_seed_rasters(seed_keys)
        logger.info(
            "Calculating %s FWI from existing rasters for %s",
            context.run_type.value,
            context.datetime_to_process.date(),
        )
        month = context.datetime_to_process.month
        # FFMC, DMC and DC each calculate forward from their own previous-day value
        ffmc_key = await FWICalculationJob(
            FFMCCalculator(), self.weather_keys, {FWIParameter.FFMC: seed_keys[FWIParameter.FFMC]}
        ).run(context)
        dmc_key = await FWICalculationJob(
            DMCCalculator(month),
            self.weather_keys,
            {FWIParameter.DMC: seed_keys[FWIParameter.DMC]},
        ).run(context)
        dc_key = await FWICalculationJob(
            DCCalculator(month), self.weather_keys, {FWIParameter.DC: seed_keys[FWIParameter.DC]}
        ).run(context)
        isi_key = await FWICalculationJob(
            ISICalculator(), self.weather_keys, {FWIParameter.FFMC: ffmc_key}
        ).run(context)
        bui_key = await FWICalculationJob(
            BUICalculator(), self.weather_keys, {FWIParameter.DMC: dmc_key, FWIParameter.DC: dc_key}
        ).run(context)
        fwi_key = await FWICalculationJob(
            FWIFinalCalculator(),
            self.weather_keys,
            {FWIParameter.ISI: isi_key, FWIParameter.BUI: bui_key},
        ).run(context)
        return {
            FWIParameter.FFMC: ffmc_key,
            FWIParameter.DMC: dmc_key,
            FWIParameter.DC: dc_key,
            FWIParameter.ISI: isi_key,
            FWIParameter.BUI: bui_key,
            FWIParameter.FWI: fwi_key,
        }


@dataclass(frozen=True)
class TemporalFuelStage(SFMSStage[GDALPath]):
    """Resolves the date's temporal fuel raster from the base fuel grid and Julian rasters,
    creating a new version when needed.

    An existing raster is reused only when it was built from the same base fuel raster and the
    same green-up and grass curing Julian date rasters, and the stored raster still matches its
    recorded hash. The Julian rasters are recorded by archive key, since the live Julian keys are
    replaced over time.
    """

    async def run(self, context: "SFMSRunContext") -> GDALPath:
        target_date = context.datetime_to_process.date()
        fuel_type_raster = context.fuel_type_raster
        raster_addresser = context.raster_addresser
        s3_client = context.s3_client

        async def _resolve() -> GDALPath:
            julian = await read_julian_rasters(s3_client, raster_addresser)
            # outside the date lock: concurrent runs would write identical bytes to the same keys
            await ensure_julian_archives(s3_client, julian)
            context.manifest.record_julian_rasters(
                {raster.name: raster.archive_key for raster in julian}
            )

            async with get_async_write_session_scope() as session:
                # held until commit so concurrent runs for the same date reuse rather than collide
                await lock_temporal_fuel_raster_date(session, target_date)
                existing = await get_matching_temporal_fuel_raster(
                    session, target_date, fuel_type_raster.id, **julian.hash_columns()
                )
                if existing is not None and await _stored_raster_matches(s3_client, existing):
                    logger.info(
                        "Reusing temporal fuel raster for %s: %s",
                        target_date,
                        existing.object_store_path,
                    )
                    return raster_addresser.gdal_path(existing.object_store_path)
                # a grid is fully determined by its inputs, so a missing or altered one is rebuilt
                # as the next version, which the reuse query then prefers

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
                        base_fuel_key=context.base_fuel_raster_path,
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

        temporal_fuel_path = await context.track(SFMSRunLogJobName.TEMPORAL_FUEL, _resolve)
        context.manifest.record_temporal_fuel_raster(temporal_fuel_path)
        return temporal_fuel_path


@dataclass(frozen=True)
class PrimaryFBPStage(SFMSStage[None]):
    """Calculates the same-day primary FBP products on the date's temporal fuel raster, from the
    run's FMC, wind, FFMC and BUI rasters."""

    temporal_fuel_path: GDALPath
    fmc_key: S3Key
    weather_keys: WeatherKeys
    fwi_keys: FWIKeys

    async def run(self, context: "SFMSRunContext") -> None:
        raster_addresser = context.raster_addresser
        slope_key = raster_addresser.get_slope_key()
        aspect_key = raster_addresser.get_aspect_key()
        context.manifest.record_static_rasters({"slope": slope_key, "aspect": aspect_key})

        async def _calculate() -> PrimaryFireBehaviourInputs:
            percent_conifer_path = await _resolve_percent_conifer_path(
                context.fuel_type_raster.year, raster_addresser, context.s3_client
            )
            context.manifest.record_percent_conifer_raster(percent_conifer_path)
            inputs = raster_addresser.get_primary_fire_behaviour_inputs(
                context.datetime_to_process,
                context.run_type,
                self.temporal_fuel_path,
                percent_conifer_path,
                raster_addresser.gdal_path(self.fwi_keys[FWIParameter.FFMC]),
                raster_addresser.gdal_path(self.fwi_keys[FWIParameter.BUI]),
                raster_addresser.gdal_path(
                    self.weather_keys[SFMSInterpolatedWeatherParameter.WIND_SPEED]
                ),
                raster_addresser.gdal_path(
                    self.weather_keys[SFMSInterpolatedWeatherParameter.WIND_DIRECTION]
                ),
                raster_addresser.gdal_path(self.fmc_key),
                raster_addresser.gdal_path(slope_key),
                raster_addresser.gdal_path(aspect_key),
            )
            await PrimaryFireBehaviourProcessor(context.datetime_to_process).process(
                context.s3_client, multi_wps_dataset_context, inputs
            )
            return inputs

        inputs = await context.track(SFMSRunLogJobName.PRIMARY_FBP_CALCULATION, _calculate)
        for parameter, output_key in inputs.output_keys.items():
            context.manifest.record_raster_output(parameter, output_key)


@dataclass(frozen=True)
class SFMSRunContext:
    """What every stage of one SFMS run for one date shares: the date and run type being
    processed, the manifest its inputs and outputs are traced in, the committed run its jobs are
    tracked against, the base fuel grid, and the clients they read and write with."""

    datetime_to_process: datetime
    run_type: RunType
    sfms_run_id: int
    manifest: SFMSRunManifest
    s3_client: S3Client
    raster_addresser: SFMSNGRasterAddresser
    fuel_type_raster: FuelTypeRaster
    seed_actual_date: date

    @property
    def base_fuel_raster_path(self) -> GDALPath:
        """The base fuel grid every stage grids its rasters to."""
        return self.raster_addresser.gdal_path(self.fuel_type_raster.object_store_path)

    @classmethod
    def start(
        cls,
        datetime_to_process: datetime,
        run_type: RunType,
        sfms_run_id: int,
        run_datetime: datetime,
        s3_client: S3Client,
        raster_addresser: SFMSNGRasterAddresser,
        *,
        fuel_type_raster: FuelTypeRaster,
        seed_actual_date: date,
        station_codes: Iterable[int],
    ) -> "SFMSRunContext":
        """Start a run, creating the manifest its inputs and outputs will be traced in.

        ``run_datetime`` is when the run was saved, and ``station_codes`` are the stations it
        interpolates from; both are the values its ``sfms_run`` row records, so a manifest and that
        row can be joined on ``run_datetime``. ``fuel_type_raster`` is the base fuel grid selected
        for the run's year, which every stage grids its rasters to. ``seed_actual_date``
        is the latest actual date the run's FWI chain is calculated forward from: the previous day
        for an actual run, and the actual date a forecast batch seeds from.
        """
        manifest = SFMSRunManifest(
            run_type=run_type,
            for_date=datetime_to_process.date(),
            run_datetime=run_datetime,
        )
        manifest.record_station_codes(station_codes)
        manifest.record_base_fuel_raster(
            raster_addresser.gdal_path(fuel_type_raster.object_store_path)
        )
        return cls(
            datetime_to_process=datetime_to_process,
            run_type=run_type,
            sfms_run_id=sfms_run_id,
            manifest=manifest,
            s3_client=s3_client,
            raster_addresser=raster_addresser,
            fuel_type_raster=fuel_type_raster,
            seed_actual_date=seed_actual_date,
        )

    def __post_init__(self):
        # a manifest that describes another run's date or type could never be joined to this one
        assert self.manifest.run_type == self.run_type, "the manifest must describe this run type"
        assert self.manifest.for_date == self.datetime_to_process.date(), (
            "the manifest must describe this target date"
        )

    async def track(self, job_name: SFMSRunLogJobName, action: Callable[[], Awaitable[T]]) -> T:
        """Run ``action`` as a job of this run, logged under ``job_name``.

        A failure is also recorded as the manifest's failed stage, under the same job name.
        """

        @track_sfms_run(job_name, self.sfms_run_id)
        async def _tracked() -> T:
            return await action()

        try:
            return await _tracked()
        except Exception as error:
            self.manifest.record_failure(job_name.value, error)
            raise

    async def write_manifest(self, error: Exception | None = None, stage: str = "") -> None:
        """Upload the manifest tracing this run's inputs and outputs.

        Given the ``error`` the run failed with, it's recorded under ``stage`` unless a stage
        already recorded the failure. The upload never raises: a run whose rasters were written
        doesn't fail over its trace, and a failed run's own error isn't masked. A failed upload is
        logged and reported to chatops instead.
        """
        if error is not None:
            self.manifest.record_failure(stage, error)
        try:
            await self.manifest.write(self.s3_client)
        except Exception as upload_error:
            message = (
                f"Failed to write SFMS run manifest for {self.run_type.value} "
                f"{self.datetime_to_process.date()}"
            )
            logger.exception(message)
            send_chatops_notification(message, upload_error)


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
