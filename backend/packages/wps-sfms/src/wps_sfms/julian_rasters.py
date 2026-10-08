"""Green-up and grass curing Julian date rasters, read and hashed for a temporal fuel build and
archived by content hash so each grid's exact inputs survive the live keys being replaced."""

import asyncio
import hashlib
import logging
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, fields

from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.utils.s3_client import S3Client

from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JulianDatasets:
    """The open green-up and grass curing Julian date rasters a temporal fuel grid is built from."""

    green_up_on: WPSDataset
    green_up_off: WPSDataset
    grass_standing: WPSDataset
    grass_matted: WPSDataset

    def by_name(self) -> dict[str, WPSDataset]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class JulianRaster:
    """A green-up or grass curing Julian date raster as read for one temporal fuel build."""

    name: str
    raster_bytes: bytes
    content_hash: str
    archive_key: S3Key


@dataclass(frozen=True)
class JulianRasters:
    """The four Julian date rasters a temporal fuel grid is built from, by name rather than by
    position so each raster's bytes, hash and archive key can't be paired with another's."""

    # field names are the S3 object names under julian/ and julian/archive/, so renaming one
    # changes where its raster is read from and archived to
    green_up_on: JulianRaster  # per-pixel Julian day green-up starts
    green_up_off: JulianRaster  # per-pixel Julian day green-up ends
    grass_standing: JulianRaster  # per-pixel Julian day grass becomes standing
    grass_matted: JulianRaster  # per-pixel Julian day grass becomes matted

    def __iter__(self) -> Iterator[JulianRaster]:
        return (getattr(self, field.name) for field in fields(self))

    @contextmanager
    def as_datasets(self) -> Generator[JulianDatasets, None, None]:
        """Open each raster from the bytes that were hashed, so a grid is always built from exactly
        what its recorded hashes describe. The datasets are closed on exit."""
        with (
            WPSDataset.from_bytes(self.green_up_on.raster_bytes) as green_up_on,
            WPSDataset.from_bytes(self.green_up_off.raster_bytes) as green_up_off,
            WPSDataset.from_bytes(self.grass_standing.raster_bytes) as grass_standing,
            WPSDataset.from_bytes(self.grass_matted.raster_bytes) as grass_matted,
        ):
            yield JulianDatasets(
                green_up_on=green_up_on,
                green_up_off=green_up_off,
                grass_standing=grass_standing,
                grass_matted=grass_matted,
            )

    def hash_columns(self) -> dict[str, str]:
        """The temporal_fuel_raster hash columns these rasters match, as column name to value."""
        return {
            TemporalFuelRaster.green_up_on_hash.key: self.green_up_on.content_hash,
            TemporalFuelRaster.green_up_off_hash.key: self.green_up_off.content_hash,
            TemporalFuelRaster.grass_standing_hash.key: self.grass_standing.content_hash,
            TemporalFuelRaster.grass_matted_hash.key: self.grass_matted.content_hash,
        }

    def archive_path_columns(self) -> dict[str, str]:
        """The temporal_fuel_raster archive path columns, as column name to archive key."""
        return {
            TemporalFuelRaster.green_up_on_archive_path.key: self.green_up_on.archive_key,
            TemporalFuelRaster.green_up_off_archive_path.key: self.green_up_off.archive_key,
            TemporalFuelRaster.grass_standing_archive_path.key: self.grass_standing.archive_key,
            TemporalFuelRaster.grass_matted_archive_path.key: self.grass_matted.archive_key,
        }


async def read_julian_rasters(
    s3_client: S3Client, raster_addresser: SFMSNGRasterAddresser
) -> JulianRasters:
    """Read and hash the current Julian date rasters."""
    names = [field.name for field in fields(JulianRasters)]
    source_keys = [raster_addresser.get_julian_key(name) for name in names]
    if not await s3_client.all_objects_exist(*source_keys):
        raise RuntimeError(f"Missing Julian date rasters, expected: {', '.join(source_keys)}")
    # Reads the four ~1.4 MB Julian rasters per date (3x per forecast run); read them once per
    # run and pass them in if they grow or more are added. A rebuild opens these same bytes, so
    # the recorded hashes always match the grid's inputs.
    all_bytes = await asyncio.gather(*(s3_client.read_object(key) for key in source_keys))
    julian_rasters = {}
    for name, raster_bytes in zip(names, all_bytes):
        content_hash = hashlib.sha256(raster_bytes).hexdigest()
        julian_rasters[name] = JulianRaster(
            name=name,
            raster_bytes=raster_bytes,
            content_hash=content_hash,
            archive_key=raster_addresser.get_julian_archive_key(name, content_hash),
        )
    return JulianRasters(**julian_rasters)


async def ensure_julian_archives(s3_client: S3Client, julian_rasters: JulianRasters) -> None:
    """Archive the exact Julian rasters by content hash, since the live keys get replaced over
    time. Only missing archives are written; an existing one already holds the same bytes."""
    archived = await asyncio.gather(
        *(s3_client.object_exists(raster.archive_key) for raster in julian_rasters)
    )
    missing = [raster for raster, exists in zip(julian_rasters, archived) if not exists]
    if not missing:
        return
    await asyncio.gather(
        *(s3_client.put_object(raster.archive_key, raster.raster_bytes) for raster in missing)
    )
    logger.info(
        "Archived Julian date rasters: %s", ", ".join(raster.archive_key for raster in missing)
    )
