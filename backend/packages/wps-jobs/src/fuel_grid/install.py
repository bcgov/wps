import logging
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import aiofiles
import numpy as np
from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from osgeo import ogr
from shapely import wkb as shapely_wkb
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    count_advisory_shape_fuel_duplicates,
    count_rows_by_fuel_type_raster_id,
    get_fire_zone_unit_shape_type_id,
    get_fire_zone_units,
    get_fuel_types_id_dict,
)
from wps_shared.db.crud.fuel_layer import get_ready_fuel_type_raster_by_year_and_hash
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryShapeFuels,
    CombustibleArea,
    FuelType,
    Shape,
    TPIFuelArea,
)
from wps_shared.db.models.fuel_type_raster import FuelRasterInstallStatus, FuelTypeRaster
from wps_shared.fuel_raster import process_fuel_type_raster
from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

from fuel_grid.combustible_area import calculate_combustible_area_by_fire_zone
from fuel_grid.fuel_masked_tpi import prepare_masked_tif
from fuel_grid.fuel_type_area import calculate_fuel_type_areas_per_zone
from fuel_grid.fuel_type_layer import fuel_type_iterator_by_key
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
    advisory_fuel_types: int
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


async def populate_static_fuel_grid_data(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    fuel_masked_tpi_key: str,
) -> FuelGridInstallCounts:
    fuel_raster_key = get_versioned_fuel_raster_key(fuel_type_raster.object_store_path)
    tpi_filename = fuel_masked_tpi_key.removeprefix("dem/tpi/")
    zones = await get_fire_zone_unit_shapes(session)

    fuel_type_rows = populate_advisory_fuel_types(session, fuel_type_raster, fuel_raster_key)
    await populate_advisory_shape_fuels(session, fuel_type_raster, fuel_raster_key, zones)
    populate_combustible_area(session, fuel_type_raster, zones, fuel_type_rows)
    populate_tpi_fuel_area(session, fuel_type_raster, tpi_filename, zones)
    # flush derived rows so verification can query them before the transaction commits.
    await session.flush()
    return await verify_static_fuel_grid_data(session, fuel_type_raster.id)


async def get_fire_zone_unit_shapes(session: AsyncSession) -> Sequence[Shape]:
    shape_type_id = await get_fire_zone_unit_shape_type_id(session)
    return await get_fire_zone_units(session, shape_type_id)


def populate_advisory_fuel_types(
    session: AsyncSession, fuel_type_raster: FuelTypeRaster, fuel_raster_key: str
) -> list[FuelType]:
    fuel_type_rows = []
    for fuel_type_id, geom in fuel_type_iterator_by_key(fuel_raster_key):
        fuel_type = FuelType(
            fuel_type_id=fuel_type_id,
            geom=geom,
            fuel_type_raster_id=fuel_type_raster.id,
        )
        session.add(fuel_type)
        fuel_type_rows.append(fuel_type)
    return fuel_type_rows


async def populate_advisory_shape_fuels(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    fuel_raster_key: str,
    zones: Sequence[Shape],
) -> None:
    sfms_fuel_types = await get_fuel_types_id_dict(session)
    all_zone_data = calculate_fuel_type_areas_per_zone(fuel_raster_key, zones)
    for zone_data in all_zone_data:
        for advisory_shape_id, fuel_type_id, fuel_area in zone_data:
            session.add(
                AdvisoryShapeFuels(
                    advisory_shape_id=advisory_shape_id,
                    fuel_type=sfms_fuel_types[int(fuel_type_id)],
                    fuel_area=fuel_area,
                    fuel_type_raster_id=fuel_type_raster.id,
                )
            )


def populate_combustible_area(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    zones: Sequence[Shape],
    fuel_type_rows: list[FuelType],
) -> None:
    combustible_fuel_type_rows = [
        fuel_type
        for fuel_type in fuel_type_rows
        if fuel_type.fuel_type_id < 99 and fuel_type.fuel_type_id > 0
    ]

    with fuel_types_layer_from_rows(combustible_fuel_type_rows) as fuel_types:
        for _, area, advisory_shape_id in calculate_combustible_area_by_fire_zone(
            fuel_types, zones
        ):
            if advisory_shape_id is None or area is None:
                continue
            session.add(
                CombustibleArea(
                    advisory_shape_id=advisory_shape_id,
                    combustible_area=area,
                    fuel_type_raster_id=fuel_type_raster.id,
                )
            )


def populate_tpi_fuel_area(
    session: AsyncSession,
    fuel_type_raster: FuelTypeRaster,
    tpi_filename: str,
    zones: Sequence[Shape],
) -> None:
    for advisory_shape_id, tpi_class, fuel_area in calculate_masked_tpi_areas(zones, tpi_filename):
        session.add(
            TPIFuelArea(
                advisory_shape_id=advisory_shape_id,
                tpi_class=tpi_class,
                fuel_area=float(
                    fuel_area.item() if isinstance(fuel_area, np.generic) else fuel_area
                ),
                fuel_type_raster_id=fuel_type_raster.id,
            )
        )


# in-memory geometry conversion for combustible-area calculation


@contextmanager
def fuel_types_layer_from_db(session_rows):
    with fuel_types_layer_from_rows(session_rows) as fuel_types:
        yield fuel_types


@contextmanager
def fuel_types_layer_from_rows(fuel_type_rows):
    mem_driver = ogr.GetDriverByName("MEM")
    mem_ds = mem_driver.CreateDataSource("fuel_types")
    fuel_types_layer = mem_ds.CreateLayer("fuel_types", geom_type=ogr.wkbPolygon)
    fuel_types_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
    fuel_types_layer.CreateField(ogr.FieldDefn("fuel_type_id", ogr.OFTInteger))

    for index, row in enumerate(fuel_type_rows, start=1):
        shapely_obj = fuel_type_geom_to_shape(row.geom)
        feature = ogr.Feature(fuel_types_layer.GetLayerDefn())
        feature.SetGeometry(ogr.CreateGeometryFromWkt(shapely_obj.wkt))
        feature.SetField("id", row.id if row.id is not None else index)
        feature.SetField("fuel_type_id", row.fuel_type_id)
        fuel_types_layer.CreateFeature(feature)
        feature = None

    try:
        yield fuel_types_layer
    finally:
        mem_ds = None


def fuel_type_geom_to_shape(geom):
    # unflushed GeoAlchemy geometry values are still hex EWKB strings at this point.
    if isinstance(geom, str):
        return shapely_wkb.loads(geom, hex=True)
    if isinstance(geom, bytes):
        return shapely_wkb.loads(geom)
    if isinstance(geom, WKBElement | WKTElement):
        return to_shape(geom)
    raise TypeError(f"Unsupported fuel type geometry: {type(geom).__name__}")


# verification


async def verify_static_fuel_grid_data(
    session: AsyncSession, fuel_type_raster_id: int
) -> FuelGridInstallCounts:
    counts = FuelGridInstallCounts(
        advisory_fuel_types=await count_rows_by_fuel_type_raster_id(
            session, FuelType, fuel_type_raster_id
        ),
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
        counts.advisory_fuel_types == 0
        or counts.advisory_shape_fuels == 0
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
