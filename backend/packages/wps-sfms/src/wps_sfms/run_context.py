"""The context every stage of one SFMS run shares.

An application of the Context Object pattern: the per-run state each stage needs is bundled into
one object passed explicitly to every stage, instead of being threaded through each stage's
signature or reached through globals. Rasters one stage hands another are passed as arguments, not
stored on the context, so stages don't depend on each other through it.
"""

import logging
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeVar

from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.sfms_run import track_sfms_run
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client

from wps_sfms.run_manifest import SFMSRunManifest
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)

T = TypeVar("T")

WeatherKeys = Mapping[SFMSInterpolatedWeatherParameter, S3Key]
"""The object store keys of the weather rasters a run interpolated, by parameter."""

FWIKeys = Mapping[FWIParameter, S3Key]
"""The object store keys of FWI index rasters, by parameter."""


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
