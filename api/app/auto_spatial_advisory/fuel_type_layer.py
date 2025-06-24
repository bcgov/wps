"""Functions for manipulating the BC Fuel Type Layer"""

import asyncio
import logging
from typing import Generator, Tuple

from osgeo import gdal, ogr, osr
from shapely import wkb, wkt
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import save_fuel_type
from wps_shared.db.crud.fuel_layer import (
    get_latest_fuel_type_raster_by_fuel_raster_name,
    get_processed_fuel_raster_details,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import FuelType
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS
from wps_shared.utils.polygonize import polygonize_in_memory

logger = logging.getLogger(__name__)


async def get_current_fuel_type_raster(session: AsyncSession):
    """
    Gets the FuelTypeRaster record for the most recent version of the fuel raster
    that matches the env FUEL_RASTER_NAME
    :param session: An async database session.
    :return: A FuelTypeRaster record.
    """
    # get fuel_type_raster record based on current value of the FUEL_RASTER_NAME env variable
    name = config.get("FUEL_RASTER_NAME")
    fuel_raster_name = name.lower()[:-4]
    fuel_type_raster = await get_latest_fuel_type_raster_by_fuel_raster_name(
        session, fuel_raster_name
    )
    return fuel_type_raster


async def get_fuel_type_raster_by_year(session: AsyncSession, year: int):
    fuel_raster_name = config.get("FUEL_RASTER_NAME")
    if year >= 2025 and str(year) not in fuel_raster_name:
        # Covers the case where we have been using last year's fuel grid in the early part of the
        # current fire season (ie. the fuel grid hasn't been updated yet).
        # Note: This assumes we are never more than one year behind. If this assumption turns out
        # to be invalid, we may need to use a regex to full the year out of the FUEL_RASTER_NAME
        # env.
        return await get_processed_fuel_raster_details(session, year - 1, None)
    return await get_processed_fuel_raster_details(session, year, None)


def fuel_type_iterator(fuel_grid_filename: str) -> Generator[Tuple[int, str], None, None]:
    """
    Yields fuel type id and geom by polygonizing fuel type layer raster stored in S3, and then
    iterating over feature from the resultant layer.

    NOTE: This works fine with a small FTL file, such as the SFMS one, but the the high resolution
    FTL file sucks up a large amount of memory when polygonizing.
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    # Hard coded for a geotiff on our S3 server, but this could be replaced by any raster file
    # that gdal is able to read.
    key = f"/vsis3/{bucket}/sfms/static/{fuel_grid_filename}"
    return fuel_type_iterator_by_key(key)


def fuel_type_iterator_by_key(fuel_type_raster_key: str) -> Generator[Tuple[int, str], None, None]:
    """
    Yields fuel type id and geom by polygonizing fuel type layer raster stored in S3, and then
    iterating over feature from the resultant layer.

    NOTE: This works fine with a small FTL file, such as the SFMS one, but the the high resolution
    FTL file sucks up a large amount of memory when polygonizing.
    """
    gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", config.get("OBJECT_STORE_SECRET"))
    gdal.SetConfigOption("AWS_ACCESS_KEY_ID", config.get("OBJECT_STORE_USER_ID"))
    gdal.SetConfigOption("AWS_S3_ENDPOINT", config.get("OBJECT_STORE_SERVER"))
    gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")
    logger.info("Polygonizing %s...", fuel_type_raster_key)
    with polygonize_in_memory(fuel_type_raster_key, "fuel", "fuel") as layer:
        spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
        coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

        logger.info("Iterating over features and inserting into database...")
        for i in range(layer.GetFeatureCount()):
            feature: ogr.Feature = layer.GetFeature(i)
            fuel_type_id = feature.GetField(0)
            geometry: ogr.Geometry = feature.GetGeometryRef()
            # Make sure the geometry is in EPSG:3005!
            geometry.Transform(coordinate_transform)
            polygon = wkt.loads(geometry.ExportToIsoWkt())
            geom = wkb.dumps(polygon, hex=True, srid=NAD83_BC_ALBERS)
            yield (fuel_type_id, geom)


async def inject_ftl_into_database():
    """This function will inject the fuel type layer into the database.
    NOTE: This function is technically redundant, as the fuel type layer is already loaded
    into the database as part of an alembic migration. However, this function remains here for
    reference as there should be some process in place that consumes the most recent fuel type
    layer and updates our database accordingly.
    """
    logger.info("save to database")
    async with get_async_write_session_scope() as session:
        for fuel_type_id, geom in fuel_type_iterator("fbp2024.tif"):
            fuel_type = FuelType(fuel_type_id=fuel_type_id, geom=geom)
            await save_fuel_type(session, fuel_type)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(inject_ftl_into_database())
