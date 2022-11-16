""" Functions for manipulating the BC Fuel Type Layer
"""
import asyncio
from typing import Generator, Tuple
import logging
from osgeo import ogr, osr, gdal
from shapely import wkt, wkb
from app import config
from auto_spatial_advisory.polygonize import polygonize_in_memory
from db.models.auto_spatial_advisory import FuelType
from db.database import get_async_write_session_scope
from db.crud.auto_spatial_advisory import save_fuel_type
from app.geospatial import NAD83_BC_ALBERS


logger = logging.getLogger(__name__)


def fuel_type_iterator() -> Generator[Tuple[int, str], None, None]:
    """
    Yields fuel type id and geom by polygonizing fuel type layer raster stored in S3, and then
    iterating over feature from the resultant layer.

    NOTE: This works fine with a small FTL file, such as the SFMS one, but the the high resolution
    FTL file sucks up a large amount of memory when polygonizing.
    """
    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')
    bucket = config.get('OBJECT_STORE_BUCKET')
    # Hard coded for a geotiff on our S3 server, but this could be replaced by any raster file
    # that gdal is able to read.
    filename = f'/vsis3/{bucket}/sfms/static/fbp2021.tif'
    logger.info('Polygonizing %s...', filename)
    with polygonize_in_memory(filename) as layer:

        spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
        coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

        logger.info('Iterating over features and inserting into database...')
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
    """ This function will inject the fuel type layer into the database.
    NOTE: This function is technically redundant, as the fuel type layer is already loaded
    into the database as part of an alembic migration. However, this function remains here for
    reference as there should be some process in place that consumes the most recent fuel type
    layer and updates our database accordingly.
    """
    logger.info('save to database')
    async with get_async_write_session_scope() as session:
        for fuel_type_id, geom in fuel_type_iterator():
            fuel_type = FuelType(fuel_type_id=fuel_type_id, geom=geom)
            await save_fuel_type(session, fuel_type)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(inject_ftl_into_database())
