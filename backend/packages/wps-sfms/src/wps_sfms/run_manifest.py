"""Input and output manifests tracing what each SFMS run read and wrote.

Rasters are overwritten in place by every daily run and backfill, so each SFMS run writes one
manifest recording the inputs and outputs it used. Manifests are stored under ``sfms_ng/runs/``
keyed by the run datetime, so a run can be traced and debugged long after its rasters are
replaced. The schema is versioned: every manifest records the ``version`` it was written with,
and ``docs/SFMS_RUN_TRACING.md`` documents the layout parsers can rely on.
"""

import logging
from collections.abc import Iterable, Mapping
from datetime import date, datetime

from pydantic import BaseModel, Field

from wps_shared import config
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
"""Schema version of the manifest this package writes."""


def object_store_key(path: str) -> str:
    """Return the plain object store key for a plain key or a GDAL /vsis3/{bucket}/ path."""
    return path.removeprefix(f"/vsis3/{config.get('OBJECT_STORE_BUCKET')}/")


class FuelRasterTrace(BaseModel):
    """The fuel rasters one SFMS run used, as object store keys."""

    base: str | None = None
    temporal: str | None = None
    pc: str | None = None


class SFMSRunInputs(BaseModel):
    """What one SFMS run read: station codes and the object store keys it consumed."""

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

    One manifest is written per SFMS run at
    ``sfms_ng/runs/{run_datetime yyyy/mm/dd}/{run_type}/{for_date}_{run_datetime}_run.json``.
    Keying by run datetime means re-runs and backfills of a target date never overwrite an
    earlier manifest. ``run_datetime`` is serialized as ISO 8601 UTC, ``for_date`` as an ISO
    date, and every raster path as a plain object store key in the manifest's own bucket.
    """

    version: int = MANIFEST_SCHEMA_VERSION
    run_datetime: datetime
    run_type: RunType
    for_date: date
    input: SFMSRunInputs = Field(default_factory=SFMSRunInputs)
    output: SFMSRunOutputs = Field(default_factory=SFMSRunOutputs)

    def record_station_codes(self, station_codes: Iterable[int]) -> None:
        """Record the station codes whose weather the run interpolated."""
        self.input.station_codes = list(station_codes)

    def record_base_fuel_raster(self, key: str) -> None:
        """Record the base fuel grid the run selected for its year."""
        self.input.fuel_raster.base = object_store_key(key)

    def record_percent_conifer_raster(self, key: str) -> None:
        """Record the percent-conifer raster paired with the base fuel grid's year."""
        self.input.fuel_raster.pc = object_store_key(key)

    def record_temporal_fuel_raster(
        self, raster_path: GDALPath, julian_archive_keys: Mapping[str, S3Key]
    ) -> None:
        """Record the temporal fuel grid the run resolved for the target date.

        The grid is recorded as both an input and an output: it is the fuel raster primary FBP
        ran on, and it is stored under this run's date. The Julian date rasters its grid was
        built from are recorded by their archive keys, since the live Julian keys are replaced
        over time.
        """
        fuel_key = object_store_key(raster_path)
        self.input.fuel_raster.temporal = fuel_key
        self.output.fuel_raster = fuel_key
        self.record_julian_rasters(julian_archive_keys)

    def record_fmc_inputs(
        self, fmc_inputs: FoliarMoistureContentInputs, target_date: date
    ) -> None:
        """Record the shared FMC raster ensured for the target date and its static rasters.

        FMC is recorded as both an input and an output: the run is responsible for the target
        date's raster, and primary FBP consumes it.
        """
        fmc_key = object_store_key(fmc_inputs.output_keys[target_date])
        self.input.fmc_raster = fmc_key
        self.output.fmc_raster = fmc_key
        self.record_static_rasters(
            {
                "elevation": fmc_inputs.elevation_key,
                "latitude": fmc_inputs.latitude_key,
                "longitude": fmc_inputs.longitude_key,
            }
        )

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
        """Upload this manifest to the object store."""
        key = self.key()
        body = self.model_dump_json(indent=2, exclude_none=True).encode()
        await s3_client.put_object(key=key, body=body)
        logger.info("Wrote SFMS run manifest: %s", key)
