import sys
from osgeo import gdal, ogr
import numpy as np
from datetime import datetime

"""
calculate_combustible_land_area.py iterates calculates the total land area covered by combustible
fuels in each fire zone, given input vector files for fuel_types and fire_zones.

In order to run this script, the input shapefiles for fire zones and fuel types must be in vector
format, and must use BC Albers (EPSG:3005) coordinate system. 

To convert the coordinates of a .shp or .tif file into EPSG:3005, use the
transform_to_epsg_3005.py script before running this script.

To convert a raster (.tif) file to a vector (.shp) file, use the
polygonize_geotiff.py script before running this script.
"""


def calculate_combustible_area_by_fire_zone(fuel_types_vector_filename, fire_zones_vector_filename):
    start_time = datetime.now()

    driver = ogr.GetDriverByName('ESRI Shapefile')
    fuel_types = driver.Open(fuel_types_vector_filename, gdal.GA_ReadOnly)
    fuel_types_layer = fuel_types.GetLayer()
    fire_zones = driver.Open(fire_zones_vector_filename, gdal.GA_ReadOnly)
    fire_zones_layer = fire_zones.GetLayer()

    print('Unfiltered feature count: {}'.format(fuel_types_layer.GetFeatureCount()))
    # Filter out non-combustible fuel types
    fuel_types_layer.SetAttributeFilter('"Band 1" > 0 and ("Band 1" < 99 or "Band 1" > 103)')
    print('Filtered feature count: {}'.format(fuel_types_layer.GetFeatureCount()))

    print('Analyzing {} fire zones in {}'.format(fire_zones_layer.GetFeatureCount(), fire_zones_vector_filename))
    print('Analyzing {} fuel type polygons in {}\n'.format(
        fuel_types_layer.GetFeatureCount(), fuel_types_vector_filename))

    for feature in fire_zones_layer:
        zone_name = feature.GetField('MFFRZNNM')
        zone_id = feature.GetField('MFFRZND')
        zone_area_sqm = feature.GetField('AREA_SQM')
        zone_geom = feature.geometry()

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
            print('{} has {} sq.m. of combustible land - {:.2f}% of its total area.'.format(zone_name,
                  intersect_area, 100 * intersect_area / zone_area_sqm))

    delta = datetime.now() - start_time
    print('\nScript took {} seconds to run.'.format(delta.seconds))


if __name__ == '__main__':
    calculate_combustible_area_by_fire_zone('fuel_types_epsg_3005.shp', 'fire_zones_epsg_3005.shp')
