import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    count_advisory_shape_fuel_duplicates,
    count_rows_by_fuel_type_raster_id,
    get_advisory_shape_ids_by_source_identifier,
    get_fuel_types_id_dict,
)
from wps_shared.db.crud.fuel_layer import get_ready_fuel_type_raster_by_year_and_hash
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryShapeFuels,
    CombustibleArea,
    TPIFuelArea,
)
from wps_shared.db.models.fuel_type_raster import FuelRasterInstallStatus, FuelTypeRaster
from wps_shared.fuel_raster import process_fuel_type_raster
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

from fuel_grid.combustible_area import calculate_combustible_area_by_fire_zone
from fuel_grid.fuel_masked_tpi import prepare_masked_tif
from fuel_grid.fuel_type_area import calculate_fuel_type_areas_per_zone
from fuel_grid.tpi_fuel_area import calculate_masked_tpi_areas

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InstalledFuelRaster:
    id: int
    year: int
    version: int
    object_store_path: str
    content_hash: str
    install_status: str


@dataclass(frozen=True)
class ProcessedFuelRaster:
    year: int
    version: int
    xsize: int
    ysize: int
    object_store_path: str
    content_hash: str
    create_timestamp: datetime


@dataclass(frozen=True)
class FuelGridInstallCounts:
    advisory_shape_fuels: int
    combustible_area: int
    tpi_fuel_area: int
    advisory_shape_fuels_duplicates: int


@dataclass(frozen=True)
class FuelGridInstallResult:
    fuel_type_raster: InstalledFuelRaster
    staged_source_key: str
    fuel_masked_tpi_key: str
    counts: FuelGridInstallCounts


async def install_fuel_grid(year: int, key: str) -> FuelGridInstallResult | None:
    """
    Install a staged fuel grid into object storage and the database.

    :param year: Fuel grid year.
    :param key: Staged object name under sfms/static/.
    :return: Install result when new database rows are populated, or None when a ready
        fuel_type_raster row already exists for the same year and raster content.
    """
    raster_addresser = BaseRasterAddresser()
    staged_source_key = raster_addresser.get_unprocessed_fuel_raster_key(key)
    processed_raster = None
    fuel_masked_tpi_key = None
    created_fuel_raster = False
    created_fuel_masked_tpi = False
    try:
        source_hash = await get_staged_fuel_raster_hash(staged_source_key)
        async with get_async_write_session_scope() as session:
            existing_fuel_raster = await get_ready_fuel_type_raster_by_year_and_hash(
                session, year, source_hash
            )
            if existing_fuel_raster is not None:
                installed_fuel_raster = installed_fuel_raster_from_record(existing_fuel_raster)
                fuel_masked_tpi_key = get_fuel_masked_tpi_key_for_version(
                    installed_fuel_raster.year, installed_fuel_raster.version
                )
                log_existing_fuel_grid_install(
                    installed_fuel_raster, staged_source_key, fuel_masked_tpi_key
                )
                return None

        processed_raster, created_fuel_raster = await get_or_create_processed_fuel_raster(
            year, key, raster_addresser, source_hash
        )
        fuel_masked_tpi_key = get_fuel_masked_tpi_key(processed_raster)
        created_fuel_masked_tpi = await ensure_fuel_masked_tpi_raster(
            processed_raster, fuel_masked_tpi_key
        )

        async with get_async_write_session_scope() as session:
            installed_fuel_raster, counts = await install_static_fuel_grid_data(
                session, processed_raster, fuel_masked_tpi_key
            )
    except Exception:
        await cleanup_object_store_artifacts(
            processed_raster if created_fuel_raster else None,
            fuel_masked_tpi_key if created_fuel_masked_tpi else None,
        )
        raise

    return FuelGridInstallResult(
        fuel_type_raster=installed_fuel_raster,
        staged_source_key=staged_source_key,
        fuel_masked_tpi_key=fuel_masked_tpi_key,
        counts=counts,
    )


def log_existing_fuel_grid_install(
    fuel_type_raster: InstalledFuelRaster, staged_source_key: str, fuel_masked_tpi_key: str
) -> None:
    logger.warning(
        "Fuel grid install skipped: ready fuel raster already exists for year %s "
        "with matching content hash",
        fuel_type_raster.year,
    )
    logger.info("fuel_type_raster_id: %s", fuel_type_raster.id)
    logger.info("year: %s", fuel_type_raster.year)
    logger.info("version: %s", fuel_type_raster.version)
    logger.info("install_status: %s", fuel_type_raster.install_status)
    logger.info("staged_source_key: %s", staged_source_key)
    logger.info("processed_raster_key: %s", fuel_type_raster.object_store_path)
    logger.info("content_hash: %s", fuel_type_raster.content_hash)
    logger.info("fuel_masked_tpi_key: %s", fuel_masked_tpi_key)


# object-store raster processing


async def get_or_create_processed_fuel_raster(
    year: int,
    key: str,
    raster_addresser: BaseRasterAddresser,
    source_hash: str,
) -> tuple[ProcessedFuelRaster, bool]:
    """
    Return versioned fuel raster metadata for the staged source raster.

    Reuses an existing versioned object when the staged source hash already exists in S3. Only
    creates a new versioned object when the content is new.

    :param year: Fuel grid year.
    :param key: Staged object name under sfms/static/.
    :param raster_addresser: Helper for fuel raster S3 keys.
    :param source_hash: Content hash of the staged source raster.
    :return: Processed raster metadata and a flag that is True only when this call created a new
        versioned fuel raster object in S3.
    """
    existing_raster = await find_versioned_fuel_raster_by_hash(year, raster_addresser, source_hash)
    if existing_raster is not None:
        logger.info(
            "Reusing existing versioned fuel raster for year %s with matching content hash: %s",
            year,
            existing_raster.object_store_path,
        )
        return existing_raster, False

    return await process_fuel_type_raster_for_install(year, key, raster_addresser), True


async def find_versioned_fuel_raster_by_hash(
    year: int, raster_addresser: BaseRasterAddresser, content_hash: str
) -> ProcessedFuelRaster | None:
    """
    Find an existing versioned fuel raster object with the requested content hash.

    :param year: Fuel grid year.
    :param raster_addresser: Helper for fuel raster S3 keys.
    :param content_hash: Content hash to match.
    :return: Processed raster metadata for the first matching versioned object, or None when no
        matching object exists before the first missing version.
    """
    start_datetime = datetime(year, 1, 1, tzinfo=timezone.utc)
    version = 1

    async with S3Client() as s3_client:
        while True:
            object_store_path = raster_addresser.get_fuel_raster_key(start_datetime, version)
            if not await s3_client.object_exists(object_store_path):
                return None

            if await s3_client.get_content_hash(object_store_path) == content_hash:
                return await processed_fuel_raster_from_s3(
                    s3_client, year, version, object_store_path, content_hash
                )

            version += 1


async def processed_fuel_raster_from_s3(
    s3_client: S3Client,
    year: int,
    version: int,
    object_store_path: str,
    content_hash: str,
) -> ProcessedFuelRaster:
    """
    Build processed fuel raster metadata from an existing versioned S3 object.

    :param s3_client: S3 client with an active async context.
    :param year: Fuel grid year.
    :param version: Version number encoded in the object path.
    :param object_store_path: Versioned fuel raster S3 key.
    :param content_hash: Expected content hash for the object.
    :return: Processed raster metadata suitable for database population.
    """
    raster_bytes = await s3_client.get_fuel_raster(object_store_path, content_hash)
    with WPSDataset.from_bytes(raster_bytes) as raster_ds:
        gdal_dataset = raster_ds.as_gdal_ds()
        xsize = gdal_dataset.RasterXSize
        ysize = gdal_dataset.RasterYSize

    return ProcessedFuelRaster(
        year=year,
        version=version,
        xsize=xsize,
        ysize=ysize,
        object_store_path=object_store_path,
        content_hash=content_hash,
        create_timestamp=get_utc_now(),
    )


async def process_fuel_type_raster_for_install(
    year: int, key: str, raster_addresser: BaseRasterAddresser
) -> ProcessedFuelRaster:
    """
    Copy the staged raster into the next versioned S3 key and return its metadata.

    :param year: Fuel grid year.
    :param key: Staged object name under sfms/static/.
    :param raster_addresser: Helper for fuel raster S3 keys.
    :return: Metadata for the newly created versioned fuel raster object.
    """
    staged_key = raster_addresser.get_unprocessed_fuel_raster_key(key)
    async with S3Client() as s3_client:
        if not await s3_client.object_exists(staged_key):
            raise FileNotFoundError(f"Fuel raster source object does not exist: {staged_key}")

    start_datetime = datetime(year, 1, 1, tzinfo=timezone.utc)
    (
        processed_year,
        version,
        xsize,
        ysize,
        object_store_path,
        processed_content_hash,
        create_timestamp,
    ) = await process_fuel_type_raster(raster_addresser, start_datetime, key)

    return ProcessedFuelRaster(
        year=processed_year,
        version=version,
        xsize=xsize,
        ysize=ysize,
        object_store_path=object_store_path,
        content_hash=processed_content_hash,
        create_timestamp=create_timestamp,
    )


async def get_staged_fuel_raster_hash(staged_key: str) -> str:
    """
    Validate that the staged source raster exists and return its content hash.

    :param staged_key: S3 key for the staged source raster.
    :return: Content hash for the staged source raster.
    """
    async with S3Client() as s3_client:
        if not await s3_client.object_exists(staged_key):
            raise FileNotFoundError(f"Fuel raster source object does not exist: {staged_key}")
        return await s3_client.get_content_hash(staged_key)


async def generate_fuel_masked_tpi_raster(fuel_type_raster: ProcessedFuelRaster) -> str:
    """
    Generate the static fuel-masked TPI raster for a processed fuel grid.

    :param fuel_type_raster: Metadata for the processed fuel raster.
    :return: S3 key for the generated fuel-masked TPI raster.
    """
    masked_tpi_key = get_fuel_masked_tpi_key(fuel_type_raster)
    async with S3Client() as s3_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            masked_tpi_path = prepare_masked_tif(temp_dir, fuel_type_raster.object_store_path)
            async with aiofiles.open(masked_tpi_path, "rb") as masked_tpi:
                await s3_client.put_object(key=masked_tpi_key, body=await masked_tpi.read())
    return masked_tpi_key


async def ensure_fuel_masked_tpi_raster(
    fuel_type_raster: ProcessedFuelRaster, masked_tpi_key: str
) -> bool:
    """
    Ensure the fuel-masked TPI raster exists for the processed fuel grid.

    :param fuel_type_raster: Metadata for the processed fuel raster.
    :param masked_tpi_key: S3 key where the fuel-masked TPI raster should exist.
    :return: True when this call generated and uploaded the raster, False when an existing S3
        object was reused.
    """
    async with S3Client() as s3_client:
        if await s3_client.object_exists(masked_tpi_key):
            logger.info("Reusing existing fuel-masked TPI raster: %s", masked_tpi_key)
            return False

    await generate_fuel_masked_tpi_raster(fuel_type_raster)
    return True


def get_fuel_masked_tpi_key(fuel_type_raster: ProcessedFuelRaster) -> str:
    return get_fuel_masked_tpi_key_for_version(fuel_type_raster.year, fuel_type_raster.version)


def get_fuel_masked_tpi_key_for_version(year: int, version: int) -> str:
    filename = get_fuel_masked_tpi_filename(year, version)
    return f"dem/tpi/{filename}"


def get_fuel_masked_tpi_filename(year: int, version: int) -> str:
    classified_tpi_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    classified_tpi_base, _ = os.path.splitext(classified_tpi_name)
    return f"{classified_tpi_base}_fuel_masked_{year}_v{version}.tif"


# database install lifecycle


async def install_static_fuel_grid_data(
    session: AsyncSession,
    processed_raster: ProcessedFuelRaster,
    fuel_masked_tpi_key: str,
) -> tuple[InstalledFuelRaster, FuelGridInstallCounts]:
    fuel_type_raster = await create_fuel_type_raster_record(session, processed_raster)
    counts = await populate_static_fuel_grid_data(session, fuel_type_raster, fuel_masked_tpi_key)
    return mark_fuel_type_raster_ready(fuel_type_raster), counts


async def create_fuel_type_raster_record(
    session: AsyncSession, processed_raster: ProcessedFuelRaster
) -> FuelTypeRaster:
    fuel_type_raster = FuelTypeRaster(
        year=processed_raster.year,
        version=processed_raster.version,
        xsize=processed_raster.xsize,
        ysize=processed_raster.ysize,
        object_store_path=processed_raster.object_store_path,
        content_hash=processed_raster.content_hash,
        create_timestamp=processed_raster.create_timestamp,
        install_status=FuelRasterInstallStatus.INSTALLING,
    )
    session.add(fuel_type_raster)
    # flush the parent row now so FK-only derived rows can reference it safely.
    await session.flush()
    return fuel_type_raster


def mark_fuel_type_raster_ready(fuel_type_raster: FuelTypeRaster) -> InstalledFuelRaster:
    fuel_type_raster.install_status = FuelRasterInstallStatus.READY
    fuel_type_raster.ready_timestamp = get_utc_now()
    return installed_fuel_raster_from_record(fuel_type_raster)


def installed_fuel_raster_from_record(fuel_type_raster: FuelTypeRaster) -> InstalledFuelRaster:
    return InstalledFuelRaster(
        id=fuel_type_raster.id,
        year=fuel_type_raster.year,
        version=fuel_type_raster.version,
        object_store_path=fuel_type_raster.object_store_path,
        content_hash=fuel_type_raster.content_hash,
        install_status=fuel_type_raster.install_status,
    )


# static derived table population


def validate_fire_zone_nodata(zone_raster_path: str) -> None:
    """Require nodata metadata before deriving static fire-zone statistics."""
    with gdal_s3_context(), WPSDataset(zone_raster_path) as zones:
        zones.require_nodata_value()


async def populate_static_fuel_grid_data(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    fuel_masked_tpi_key: str,
) -> FuelGridInstallCounts:
    fuel_raster_key = BaseRasterAddresser().gdal_path(S3Key(fuel_type_raster.object_store_path))
    masked_tpi_path = BaseRasterAddresser().gdal_path(S3Key(fuel_masked_tpi_key))
    zone_raster_path = BaseRasterAddresser().get_fire_zone_units_path()
    validate_fire_zone_nodata(zone_raster_path)
    fuel_areas = calculate_fuel_type_areas_per_zone(fuel_raster_key, zone_raster_path)
    combustible_areas = calculate_combustible_area_by_fire_zone(fuel_raster_key, zone_raster_path)
    tpi_areas = calculate_masked_tpi_areas(masked_tpi_path, zone_raster_path)
    source_to_shape_id = await get_advisory_shape_ids_by_source_identifier(session)
    observed_zone_ids = (
        {source_identifier for source_identifier, _ in fuel_areas}
        | set(combustible_areas)
        | {source_identifier for source_identifier, _ in tpi_areas}
    )
    validate_zone_ids(observed_zone_ids, source_to_shape_id)

    await populate_advisory_shape_fuels(session, fuel_type_raster, fuel_areas, source_to_shape_id)
    populate_combustible_area(session, fuel_type_raster, combustible_areas, source_to_shape_id)
    populate_tpi_fuel_area(session, fuel_type_raster, tpi_areas, source_to_shape_id)
    # flush derived rows so verification can query them before the transaction commits.
    await session.flush()
    return await verify_static_fuel_grid_data(session, fuel_type_raster.id)


def validate_zone_ids(observed_zone_ids: set[int], source_to_shape_id: dict[int, int]) -> None:
    """Validate the union of zone IDs from all derived fuel-grid calculations once."""
    unknown = observed_zone_ids - source_to_shape_id.keys()
    if unknown:
        raise ValueError(f"Fire-zone raster contains unknown source identifiers: {sorted(unknown)}")


async def populate_advisory_shape_fuels(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    fuel_areas: dict[tuple[int, int], float],
    source_to_shape_id: dict[int, int],
) -> None:
    sfms_fuel_types = await get_fuel_types_id_dict(session)
    for (source_identifier, fuel_type_id), fuel_area in fuel_areas.items():
        if fuel_type_id not in sfms_fuel_types:
            continue
        session.add(
            AdvisoryShapeFuels(
                advisory_shape_id=source_to_shape_id[source_identifier],
                fuel_type=sfms_fuel_types[fuel_type_id],
                fuel_area=fuel_area,
                fuel_type_raster_id=fuel_type_raster.id,
            )
        )


def populate_combustible_area(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    combustible_areas: dict[int, float],
    source_to_shape_id: dict[int, int],
) -> None:
    for source_identifier, area in combustible_areas.items():
        session.add(
            CombustibleArea(
                advisory_shape_id=source_to_shape_id[source_identifier],
                combustible_area=area,
                fuel_type_raster_id=fuel_type_raster.id,
            )
        )


def populate_tpi_fuel_area(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    tpi_areas: dict,
    source_to_shape_id: dict[int, int],
) -> None:
    for (source_identifier, tpi_class), fuel_area in tpi_areas.items():
        session.add(
            TPIFuelArea(
                advisory_shape_id=source_to_shape_id[source_identifier],
                tpi_class=tpi_class,
                fuel_area=fuel_area,
                fuel_type_raster_id=fuel_type_raster.id,
            )
        )


# verification


async def verify_static_fuel_grid_data(
    session: AsyncSession, fuel_type_raster_id: int
) -> FuelGridInstallCounts:
    counts = FuelGridInstallCounts(
        advisory_shape_fuels=await count_rows_by_fuel_type_raster_id(
            session, AdvisoryShapeFuels, fuel_type_raster_id
        ),
        combustible_area=await count_rows_by_fuel_type_raster_id(
            session, CombustibleArea, fuel_type_raster_id
        ),
        tpi_fuel_area=await count_rows_by_fuel_type_raster_id(
            session, TPIFuelArea, fuel_type_raster_id
        ),
        advisory_shape_fuels_duplicates=await count_advisory_shape_fuel_duplicates(
            session, fuel_type_raster_id
        ),
    )

    if (
        counts.advisory_shape_fuels == 0
        or counts.combustible_area == 0
        or counts.tpi_fuel_area == 0
    ):
        raise RuntimeError(f"Fuel grid install produced missing derived data: {counts}")
    if counts.advisory_shape_fuels_duplicates > 0:
        raise RuntimeError(
            "Fuel grid install produced duplicate advisory_shape_fuels rows: "
            f"{counts.advisory_shape_fuels_duplicates}"
        )
    return counts


# failure cleanup


async def cleanup_object_store_artifacts(
    processed_raster: ProcessedFuelRaster | None, fuel_masked_tpi_key: str | None
) -> None:
    keys = []
    if processed_raster is not None:
        keys.append(processed_raster.object_store_path)
    if fuel_masked_tpi_key is not None:
        keys.append(fuel_masked_tpi_key)

    if not keys:
        return

    try:
        # object-store writes are outside the DB transaction, so cleanup is best effort on failure.
        async with S3Client() as s3_client:
            for key in keys:
                try:
                    await s3_client.delete_object(key)
                    logger.info("Cleaned up fuel grid install object: %s", key)
                except Exception:
                    logger.warning("Could not clean up fuel grid install object: %s", key)
    except Exception:
        logger.warning("Could not create S3 client for fuel grid install cleanup", exc_info=True)
