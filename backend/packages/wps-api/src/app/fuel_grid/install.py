import logging
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

import aiofiles
import numpy as np
from geoalchemy2.elements import WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from osgeo import ogr
from shapely import wkb as shapely_wkb
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    get_fire_zone_unit_shape_type_id,
    get_fire_zone_units,
    get_fuel_types_id_dict,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryShapeFuels,
    CombustibleArea,
    FuelType,
    Shape,
    TPIFuelArea,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.fuel_raster import process_fuel_type_raster
from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3_client import S3Client

from app.auto_spatial_advisory.calculate_combustible_land_area import (
    calculate_combustible_area_by_fire_zone,
)
from app.auto_spatial_advisory.fuel_type_area import calculate_fuel_type_areas_per_zone
from app.auto_spatial_advisory.fuel_type_layer import fuel_type_iterator_by_key
from app.auto_spatial_advisory.local.generate_fuel_masked_tpi import prepare_masked_tif
from app.auto_spatial_advisory.process_tpi_fuel_area import calculate_masked_tpi_areas

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InstalledFuelRaster:
    id: int
    year: int
    version: int
    object_store_path: str
    content_hash: str
    record: FuelTypeRaster | None = field(default=None, compare=False, repr=False)


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


async def process_fuel_type_raster_for_install(
    year: int, key: str, raster_addresser: BaseRasterAddresser
) -> ProcessedFuelRaster:
    """Process the staged raster and return metadata for the next installed version."""
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


async def reserve_fuel_type_raster_id(session: AsyncSession) -> int:
    """Reserve a primary key so related rows can be staged without an early flush."""
    stmt = select(func.nextval(func.pg_get_serial_sequence("fuel_type_raster", "id")))
    result = await session.execute(stmt)
    return result.scalar_one()


async def create_fuel_type_raster_record(
    session: AsyncSession, processed_raster: ProcessedFuelRaster
) -> InstalledFuelRaster:
    fuel_type_raster_id = await reserve_fuel_type_raster_id(session)
    fuel_type_raster = FuelTypeRaster(
        id=fuel_type_raster_id,
        year=processed_raster.year,
        version=processed_raster.version,
        xsize=processed_raster.xsize,
        ysize=processed_raster.ysize,
        object_store_path=processed_raster.object_store_path,
        content_hash=processed_raster.content_hash,
        create_timestamp=processed_raster.create_timestamp,
    )
    session.add(fuel_type_raster)
    return InstalledFuelRaster(
        id=fuel_type_raster.id,
        year=fuel_type_raster.year,
        version=fuel_type_raster.version,
        object_store_path=fuel_type_raster.object_store_path,
        content_hash=fuel_type_raster.content_hash,
        record=fuel_type_raster,
    )


def get_fuel_type_raster_record(fuel_type_raster: InstalledFuelRaster) -> FuelTypeRaster:
    if fuel_type_raster.record is None:
        raise RuntimeError("Installed fuel raster is missing its staged ORM record")
    return fuel_type_raster.record


def get_fuel_masked_tpi_filename(year: int, version: int) -> str:
    classified_tpi_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    classified_tpi_base, _ = os.path.splitext(classified_tpi_name)
    return f"{classified_tpi_base}_fuel_masked_{year}_v{version}.tif"


def get_fuel_masked_tpi_key(fuel_type_raster: ProcessedFuelRaster) -> str:
    filename = get_fuel_masked_tpi_filename(fuel_type_raster.year, fuel_type_raster.version)
    return f"dem/tpi/{filename}"


async def generate_fuel_masked_tpi_raster(fuel_type_raster: ProcessedFuelRaster) -> str:
    """Generate the TPI raster masked by the selected fuel grid and return its S3 key."""
    masked_tpi_key = get_fuel_masked_tpi_key(fuel_type_raster)
    async with S3Client() as s3_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            masked_tpi_path = prepare_masked_tif(temp_dir, fuel_type_raster.object_store_path)
            async with aiofiles.open(masked_tpi_path, "rb") as masked_tpi:
                await s3_client.put_object(key=masked_tpi_key, body=await masked_tpi.read())
    return masked_tpi_key


def populate_advisory_fuel_types(
    session: AsyncSession, fuel_type_raster: InstalledFuelRaster, fuel_raster_key: str
) -> list[FuelType]:
    fuel_type_raster_record = get_fuel_type_raster_record(fuel_type_raster)
    fuel_type_rows = []
    for fuel_type_id, geom in fuel_type_iterator_by_key(fuel_raster_key):
        fuel_type = FuelType(
            fuel_type_id=fuel_type_id,
            geom=geom,
            fuel_type_raster_id=fuel_type_raster.id,
            fuel_type_raster=fuel_type_raster_record,
        )
        session.add(fuel_type)
        fuel_type_rows.append(fuel_type)
    return fuel_type_rows


async def populate_advisory_shape_fuels(
    session: AsyncSession,
    fuel_type_raster: InstalledFuelRaster,
    fuel_raster_key: str,
    zones: Sequence[Shape],
) -> None:
    fuel_type_raster_record = get_fuel_type_raster_record(fuel_type_raster)
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
                    fuel_type_raster=fuel_type_raster_record,
                )
            )


@contextmanager
def fuel_types_layer_from_db(session_rows):
    mem_driver = ogr.GetDriverByName("MEM")
    mem_ds = mem_driver.CreateDataSource("fuel_types")
    fuel_types_layer = mem_ds.CreateLayer("fuel_types", geom_type=ogr.wkbPolygon)
    fuel_types_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
    fuel_types_layer.CreateField(ogr.FieldDefn("fuel_type_id", ogr.OFTInteger))

    for index, row in enumerate(session_rows, start=1):
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
    if isinstance(geom, str):
        return shapely_wkb.loads(geom, hex=True)
    if isinstance(geom, bytes):
        return shapely_wkb.loads(geom)
    if isinstance(geom, WKBElement | WKTElement):
        return to_shape(geom)
    raise TypeError(f"Unsupported fuel type geometry: {type(geom).__name__}")


def populate_combustible_area(
    session: AsyncSession,
    fuel_type_raster: InstalledFuelRaster,
    zones: Sequence[Shape],
    fuel_type_rows: list[FuelType],
) -> None:
    fuel_type_raster_record = get_fuel_type_raster_record(fuel_type_raster)
    combustible_fuel_type_rows = [
        fuel_type
        for fuel_type in fuel_type_rows
        if fuel_type.fuel_type_id < 99 and fuel_type.fuel_type_id > 0
    ]

    with fuel_types_layer_from_db(combustible_fuel_type_rows) as fuel_types:
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
                    fuel_type_raster=fuel_type_raster_record,
                )
            )


def populate_tpi_fuel_area(
    session: AsyncSession,
    fuel_type_raster: InstalledFuelRaster,
    tpi_filename: str,
    zones: Sequence[Shape],
) -> None:
    fuel_type_raster_record = get_fuel_type_raster_record(fuel_type_raster)
    for advisory_shape_id, tpi_class, fuel_area in calculate_masked_tpi_areas(zones, tpi_filename):
        session.add(
            TPIFuelArea(
                advisory_shape_id=advisory_shape_id,
                tpi_class=tpi_class,
                fuel_area=float(
                    fuel_area.item() if isinstance(fuel_area, np.generic) else fuel_area
                ),
                fuel_type_raster_id=fuel_type_raster.id,
                fuel_type_raster=fuel_type_raster_record,
            )
        )


async def verify_static_fuel_grid_data(
    session: AsyncSession, fuel_type_raster_id: int
) -> FuelGridInstallCounts:
    counts = FuelGridInstallCounts(
        advisory_fuel_types=await count_rows(session, FuelType, fuel_type_raster_id),
        advisory_shape_fuels=await count_rows(session, AdvisoryShapeFuels, fuel_type_raster_id),
        combustible_area=await count_rows(session, CombustibleArea, fuel_type_raster_id),
        tpi_fuel_area=await count_rows(session, TPIFuelArea, fuel_type_raster_id),
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


async def count_rows(session: AsyncSession, model, fuel_type_raster_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(model)
        .where(model.fuel_type_raster_id == fuel_type_raster_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def count_advisory_shape_fuel_duplicates(
    session: AsyncSession, fuel_type_raster_id: int
) -> int:
    duplicates = (
        select(
            AdvisoryShapeFuels.advisory_shape_id,
            AdvisoryShapeFuels.fuel_type,
            AdvisoryShapeFuels.fuel_type_raster_id,
        )
        .where(AdvisoryShapeFuels.fuel_type_raster_id == fuel_type_raster_id)
        .group_by(
            AdvisoryShapeFuels.advisory_shape_id,
            AdvisoryShapeFuels.fuel_type,
            AdvisoryShapeFuels.fuel_type_raster_id,
        )
        .having(func.count() > 1)
        .subquery()
    )
    result = await session.execute(select(func.count()).select_from(duplicates))
    return result.scalar_one()


async def populate_static_fuel_grid_data(
    session: AsyncSession,
    fuel_type_raster: InstalledFuelRaster,
    fuel_masked_tpi_key: str,
) -> FuelGridInstallCounts:
    fuel_raster_key = get_versioned_fuel_raster_key(fuel_type_raster.object_store_path)
    tpi_filename = fuel_masked_tpi_key.removeprefix("dem/tpi/")
    shape_type_id = await get_fire_zone_unit_shape_type_id(session)
    zones = await get_fire_zone_units(session, shape_type_id)

    fuel_type_rows = populate_advisory_fuel_types(session, fuel_type_raster, fuel_raster_key)
    await populate_advisory_shape_fuels(session, fuel_type_raster, fuel_raster_key, zones)
    populate_combustible_area(session, fuel_type_raster, zones, fuel_type_rows)
    populate_tpi_fuel_area(session, fuel_type_raster, tpi_filename, zones)
    await session.flush()
    return await verify_static_fuel_grid_data(session, fuel_type_raster.id)


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
        async with S3Client() as s3_client:
            for key in keys:
                try:
                    await s3_client.delete_object(key)
                    logger.info("Cleaned up fuel grid install object: %s", key)
                except Exception:
                    logger.warning("Could not clean up fuel grid install object: %s", key)
    except Exception:
        logger.warning("Could not create S3 client for fuel grid install cleanup", exc_info=True)


async def install_fuel_grid(year: int, key: str) -> FuelGridInstallResult:
    raster_addresser = BaseRasterAddresser()
    processed_raster = None
    fuel_masked_tpi_key = None
    try:
        processed_raster = await process_fuel_type_raster_for_install(year, key, raster_addresser)
        fuel_masked_tpi_key = get_fuel_masked_tpi_key(processed_raster)
        await generate_fuel_masked_tpi_raster(processed_raster)

        async with get_async_write_session_scope() as session:
            fuel_type_raster = await create_fuel_type_raster_record(session, processed_raster)
            # the flush inside populate_static_fuel_grid_data is still inside this transaction;
            # if verification raises, the session scope rolls back all staged DB rows.
            counts = await populate_static_fuel_grid_data(
                session, fuel_type_raster, fuel_masked_tpi_key
            )
    except Exception:
        await cleanup_object_store_artifacts(processed_raster, fuel_masked_tpi_key)
        raise

    return FuelGridInstallResult(
        fuel_type_raster=fuel_type_raster,
        staged_source_key=raster_addresser.get_unprocessed_fuel_raster_key(key),
        fuel_masked_tpi_key=fuel_masked_tpi_key,
        counts=counts,
    )
