"""
calculate_combustible_land_area.py iterates calculates the total land area covered by combustible
fuels in each fire zone.

The fuel types vector file is retrieved from our object store bucket, and the fire zones
(simplified polygons) are pulled from our database.
"""
from contextlib import contextmanager
from typing import Generator, Tuple
import logging
from osgeo import gdal, ogr
from geoalchemy2.shape import to_shape
from app import config


logger = logging.getLogger(__name__)


@contextmanager
def get_fuel_types_from_object_store():
    """
    Fetches simplified fuel type layer shapefile from object store, filters out
    non-combustible fuel types, and returns the layer.
    """
    # Simplified fuel type layer that SFMS system uses (fbp2021.tif) has been converted to EPSG:3005,
    # polygonized, and saved to our object store bucket.
    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')
    bucket = config.get('OBJECT_STORE_BUCKET')
    fuel_types_vector_filepath = f'/vsis3/{bucket}/ftl/fuel_types_from_sfms_epsg_3005.shp'

    driver = ogr.GetDriverByName('ESRI Shapefile')
    fuel_types = driver.Open(fuel_types_vector_filepath, gdal.GA_ReadOnly)
    logger.info('Retrieving fuel types layer from %s', fuel_types_vector_filepath)
    fuel_types_layer = fuel_types.GetLayer()

    # Filter out non-combustible fuel types
    fuel_types_layer.SetAttributeFilter('"Band 1" > 0 and ("Band 1" < 99 or "Band 1" > 103)')

    yield fuel_types_layer


def calculate_combustible_area_by_fire_zone(fuel_types_layer, zones) -> Generator[Tuple[str, float], None, None]:
    """
    Given layer of combustible fuel types for BC and fire zone ID and geometry,
    calculates the intersection of zone geom and combustible fuels.
    Yields fire zone's combustible area in square metres.
    """
    for zone in zones:
        zone_wkb = zone.geom
        shapely_zone_geom = to_shape(zone_wkb)
        zone_wkt = shapely_zone_geom.wkt
        zone_geom = ogr.CreateGeometryFromWkt(zone_wkt)
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
            yield (str(zone['source_identifier']), intersection.GetArea())
        else:
            yield (None, None)
