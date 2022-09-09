from typing import Dict
import logging
from osgeo import gdal, ogr
import asyncio
from geoalchemy2 import functions
from sqlalchemy import select
from app.db.database import get_async_read_session_scope
from app.db.models.auto_spatial_advisory import Shape
from app import config


"""
calculate_combustible_land_area.py iterates calculates the total land area covered by combustible
fuels in each fire zone.

The fuel types vector file is retrieved from our object store bucket, and the fire zones
(simplified polygons) are pulled from our database.
"""

logger = logging.getLogger(__name__)


async def calculate_combustible_area_by_fire_zone():
    # Simplified fuel type layer that SFMS system uses (fbp2021.tif) has been converted to EPSG:3005,
    # polygonized, and saved to our object store bucket.
    bucket = config.get('OBJECT_STORE_BUCKET')
    fuel_types_vector_filepath = f'/vsis3/{bucket}/ftl/fuel_types_epsg_3005.shp'

    driver = ogr.GetDriverByName('ESRI Shapefile')
    fuel_types = driver.Open(fuel_types_vector_filepath, gdal.GA_ReadOnly)
    logger.info('Retrieving fuel types layer from {}'.format(fuel_types_vector_filepath))
    fuel_types_layer = fuel_types.GetLayer()

    async with get_async_read_session_scope() as session:
        stmt = select(Shape.id,
                      Shape.source_identifier,
                      functions.ST_AsText(Shape.geom).label('geom_wkt'),
                      Shape.geom.ST_Area().label('zone_area'))
        result = await session.execute(stmt)
        all_zones = result.all()

    # Filter out non-combustible fuel types
    fuel_types_layer.SetAttributeFilter('"Band 1" > 0 and ("Band 1" < 99 or "Band 1" > 103)')

    zone_combustible_area_dict: Dict[int, float] = {}

    for zone in all_zones:
        zone_geom = ogr.CreateGeometryFromWkt(zone.geom_wkt)
        fuel_types_layer.SetSpatialFilter(zone_geom)
        # create GeometryCollection of all filtered fuel type polygons
        geom_collection = ogr.Geometry(ogr.wkbGeometryCollection)
        for fuel_type_geom in fuel_types_layer:
            geom_collection.AddGeometry(fuel_type_geom.geometry())

        # ensure the GeometryCollection is valid
        geom_collection_valid = geom_collection.MakeValid()

        # this line is necessary because otherwise Fraser Fire Zone can't undergo spatial
        # comparison for calculating Intersection. Likely due to the fuel types polygons
        # self-intersecting somewhere within the Fraser Fire Zone. Buffer(0) tries to
        # correct the self-intersection by "guessing", but it isn't always right.
        # https://gis.stackexchange.com/questions/311209/how-to-fix-invalid-polygon-with-self-intersection-python
        buffered_geom_collection = geom_collection_valid.Buffer(0)

        # get intersection
        intersection = buffered_geom_collection.Intersection(zone_geom)
        if intersection is not None and intersection.GetArea() > 0:
            intersect_area = intersection.GetArea()
            zone_combustible_area_dict[zone.source_identifier] = intersect_area

    logger.info('Finished calculating combustible areas for all fire zones.')
    return zone_combustible_area_dict


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(calculate_combustible_area_by_fire_zone())
