"""Input and output manifests tracing what each SFMS run read and wrote.

Every daily run and backfill overwrites the same raster keys, so nothing on its own records which
station codes, which temporal fuel grid version, which green-up and grass curing Julian date
rasters, or which previous-day FFMC/DMC/DC seeds went into a given day's outputs. Each run
therefore writes one manifest recording the inputs and outputs it used, stored under its own run
datetime so it survives those overwrites and a run can be traced and debugged long afterwards.

The schema is versioned: every manifest records the ``version`` it was written with, and
``docs/SFMS_RUN_TRACING.md`` documents the layout parsers can rely on.
"""

import logging
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FBPParameter,
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client

from wps_sfms.raster_inputs import FoliarMoistureContentInputs
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)

MANIFEST_SCHEMA_VERSION = 1
"""The schema version of the manifest this module writes."""


def object_store_key(path: str) -> str:
    """Return the plain object store key for a plain key or a GDAL ``/vsis3/{bucket}/`` path."""
    return SFMSNGRasterAddresser().s3_key(path)


class FuelRasterTrace(BaseModel):
    """The fuel rasters one SFMS run used, as object store keys."""

    base: str | None = None
    temporal: str | None = None
    pc: str | None = None


class SFMSRunInputs(BaseModel):
    """What one SFMS run read: the station codes it interpolated and the keys it consumed."""

    station_codes: list[int] = Field(default_factory=list)
    fuel_raster: FuelRasterTrace = Field(default_factory=FuelRasterTrace)
    seed_rasters: dict[str, str] = Field(default_factory=dict)
    """Previous-day FFMC/DMC/DC rasters the run calculated FWI forward from."""
    static_rasters: dict[str, str] = Field(default_factory=dict)
    """Static rasters by role name, e.g. ``dem``, ``mask``, ``slope``."""
    julian_rasters: dict[str, str] = Field(default_factory=dict)
    """Green-up and grass curing rasters a temporal fuel grid was built from, by archive key."""
    fmc_raster: str | None = None


class SFMSRunOutputs(BaseModel):
    """The rasters one SFMS run wrote, by product."""

    weather: dict[str, str] = Field(default_factory=dict)
    fwi: dict[str, str] = Field(default_factory=dict)
    fbp: dict[str, str] = Field(default_factory=dict)
    fuel_raster: str | None = None
    fmc_raster: str | None = None


class SFMSRunManifest(BaseModel):
    """The inputs and outputs of one SFMS run, in the version 1 manifest schema.

    One manifest is written per SFMS run, at
    ``sfms_ng/runs/{run_datetime yyyy/mm/dd}/{run_type}/{for_date}_{run_datetime}_run.json``.
    Keying by run datetime means re-runs and backfills of a target date never overwrite an earlier
    manifest. ``run_datetime`` is serialized as ISO 8601 UTC, ``for_date`` as an ISO date, and
    every raster path as a plain object store key in the manifest's own bucket.
    """

    version: int = MANIFEST_SCHEMA_VERSION
    run_datetime: datetime
    run_type: RunType
    for_date: date
    status: Literal["running", "success", "failed"] = "running"
    failed_stage: str | None = None
    failure_type: str | None = None
    failure_message: str | None = None
    input: SFMSRunInputs = Field(default_factory=SFMSRunInputs)
    output: SFMSRunOutputs = Field(default_factory=SFMSRunOutputs)

    def record_failure(self, stage: str, error: Exception) -> None:
        """Record the first stage failure, without replacing an earlier failure cause."""
        if self.status != "running":
            return
        self.status = "failed"
        self.failed_stage = stage
        self.failure_type = type(error).__name__
        message = str(error).strip()
        self.failure_message = message[:512] if message else None

    def record_station_codes(self, station_codes: Iterable[int]) -> None:
        """Record the station codes whose weather the run interpolated."""
        self.input.station_codes = list(station_codes)

    def record_base_fuel_raster(self, key: str) -> None:
        """Record the base fuel grid the run selected for its year."""
        self.input.fuel_raster.base = object_store_key(key)

    def record_percent_conifer_raster(self, key: str) -> None:
        """Record the percent-conifer raster paired with the base fuel grid's year."""
        self.input.fuel_raster.pc = object_store_key(key)

    def record_temporal_fuel_raster(self, raster_path: GDALPath) -> None:
        """Record the temporal fuel grid the run resolved for the target date.

        The grid is recorded as both an input and an output: it is the fuel raster primary FBP ran
        on, and it is stored under this run's date. The Julian date rasters it was built from are
        recorded separately, with ``record_julian_rasters``.
        """
        fuel_key = object_store_key(raster_path)
        self.input.fuel_raster.temporal = fuel_key
        self.output.fuel_raster = fuel_key

    def record_fmc_static_inputs(self, fmc_inputs: FoliarMoistureContentInputs) -> None:
        """Record the static rasters used to calculate FMC."""
        self.record_static_rasters(
            {
                "elevation": fmc_inputs.elevation_key,
                "latitude": fmc_inputs.latitude_key,
                "longitude": fmc_inputs.longitude_key,
            }
        )

    def record_fmc_raster(self, fmc_inputs: FoliarMoistureContentInputs, target_date: date) -> None:
        """Record the calculated FMC raster for the target date.

        FMC is recorded as both an input and an output: the run is responsible for the target
        date's raster, and primary FBP consumes it.
        """
        fmc_key = object_store_key(fmc_inputs.output_keys[target_date])
        self.input.fmc_raster = fmc_key
        self.output.fmc_raster = fmc_key

    def record_seed_rasters(self, seed_keys: Mapping[FWIParameter, str]) -> None:
        """Record the previous-day index rasters the run calculated FWI forward from."""
        self.input.seed_rasters.update(
            {param.value: object_store_key(key) for param, key in seed_keys.items()}
        )

    def record_static_rasters(self, rasters: Mapping[str, str]) -> None:
        """Record static rasters the run read, by role name."""
        self.input.static_rasters.update(
            {name: object_store_key(key) for name, key in rasters.items()}
        )

    def record_julian_rasters(self, archive_keys: Mapping[str, str]) -> None:
        """Record the Julian date rasters a temporal fuel grid was built from, by archive key."""
        self.input.julian_rasters.update(
            {name: object_store_key(key) for name, key in archive_keys.items()}
        )

    def record_raster_output(
        self,
        parameter: SFMSInterpolatedWeatherParameter | FWIParameter | FBPParameter,
        key: str,
    ) -> None:
        """Record one published raster under the output family its parameter belongs to."""
        output_key = object_store_key(key)
        if isinstance(parameter, SFMSInterpolatedWeatherParameter):
            self.output.weather[parameter.value] = output_key
        elif isinstance(parameter, FBPParameter):
            self.output.fbp[parameter.value] = output_key
        elif isinstance(parameter, FWIParameter):
            self.output.fwi[parameter.value] = output_key
        else:
            raise ValueError(f"Unsupported raster output parameter: {parameter}")

    def key(self) -> S3Key:
        """The object store key this manifest is written to."""
        return SFMSNGRasterAddresser().get_run_manifest_key(
            self.run_type, self.for_date, self.run_datetime
        )

    async def write(self, s3_client: S3Client) -> None:
        """Upload this terminal manifest to the object store."""
        key = self.key()
        was_running = self.status == "running"
        if was_running:
            self.status = "success"
        try:
            body = self.model_dump_json(indent=2, exclude_none=True).encode()
            await s3_client.put_object(key=key, body=body)
        except Exception:
            if was_running:
                self.status = "running"
            raise
        logger.info("Wrote SFMS run manifest: %s", key)
