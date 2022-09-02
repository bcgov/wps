import os
import sys
from osgeo import gdal, osr, ogr
import numpy as np
from datetime import datetime


def transform_shapefile_to_epsg_3005(source_file, new_filename):
    """
    Transforms coordinates in source_file shapefile to EPSG:3005 (BC Albers),
    writes to newly created shapefile called <new_filename>.shp
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    source_data = driver.Open(source_file, gdal.GA_ReadOnly)

    if source_data is None:
        print('Could not open {}'.format(source_file))
        return

    source_layer = source_data.GetLayer()
    input_spatial_ref = source_layer.GetSpatialRef()

    output_spatial_ref = osr.SpatialReference()
    output_spatial_ref.ImportFromEPSG(3005)

    coords_transform = osr.CreateCoordinateTransformation(input_spatial_ref, output_spatial_ref)

    # create output layer
    output_shapefile = new_filename + '.shp'
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    output_dataset = driver.CreateDataSource(output_shapefile)
    output_layer = output_dataset.CreateLayer("epsg_3005", output_spatial_ref, geom_type=ogr.wkbMultiPolygon)

    input_layer_defn = source_layer.GetLayerDefn()
    for i in range(input_layer_defn.GetFieldCount()):
        field_defn = input_layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    output_layer_defn = output_layer.GetLayerDefn()

    # loop through input features
    input_feature = source_layer.GetNextFeature()
    while input_feature:
        # get input geometry
        geom = input_feature.GetGeometryRef()
        # reproject the geom
        geom.Transform(coords_transform)
        # create new feature
        output_feature = ogr.Feature(output_layer_defn)
        # set the geometry and attribute
        output_feature.SetGeometry(geom)
        for i in range(output_layer_defn.GetFieldCount()):
            output_feature.SetField(output_layer_defn.GetFieldDefn(i).GetNameRef(), input_feature.GetField(i))
        # add the feature to output_shapefile
        output_layer.CreateFeature(output_feature)
        # dereference the features, get next input feature
        output_feature = None
        input_feature = source_layer.GetNextFeature()

    # save and close shapefile
    source_data = None
    output_dataset = None

    print('Transformed shapefile written to {}'.format(new_filename + '.shp'))

    del source_data, output_dataset, coords_transform


def transform_geotiff_to_epsg_3005(source_file, new_filename):
    """
    Transforms coordinates in source_file geotiff to EPSG:3005 (BC Albers),
    writes to newly created geotiff called <new_filename>.tif
    """
    source_data = gdal.Open(source_file, gdal.GA_ReadOnly)
    gdal.Warp(new_filename + '.tif', source_data, dstSRS='EPSG:3005')

    # close file so it is written to disk
    source_data = None

    print('Transformed geotiff written to {}'.format(new_filename + '.tif'))

    del source_data


def polygonize_geotiff(raster_source_filename, vector_dest_filename):
    """
    Ingests the file <raster_source_filename>, creates new file called
    <vector_dest_filename>.shp, and inserts polygonized contents of source
    file into destination file.
    """
    source_data = gdal.Open(raster_source_filename, gdal.GA_ReadOnly)
    source_band = source_data.GetRasterBand(1)
    value = ogr.FieldDefn('Band 1', ogr.OFTInteger)
    print('{} raster count: {}'.format(raster_source_filename, source_data.RasterCount))

    driver = ogr.GetDriverByName("ESRI Shapefile")
    destination = driver.CreateDataSource(vector_dest_filename + ".shp")
    dest_srs = ogr.osr.SpatialReference()
    dest_srs.ImportFromEPSG(3005)
    dest_layer = destination.CreateLayer(vector_dest_filename, geom_type=ogr.wkbPolygon, srs=dest_srs)
    dest_layer.CreateField(value)
    dest_field = dest_layer.GetLayerDefn().GetFieldIndex('Band 1')
    gdal.Polygonize(source_band, None, dest_layer, dest_field, [])

    print('Polygonized {} to {}.shp'.format(raster_source_filename, vector_dest_filename))


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
        # comparison for calculating Intersection. Likely due to the Fraser polygon
        # self-intersecting somewhere. Buffer(0) tries to correct the self-intersection
        # by "guessing", but it isn't always right.
        # Confusingly, when checking IsValid() on every zone_geom, they all return True.
        # https://gis.stackexchange.com/questions/311209/how-to-fix-invalid-polygon-with-self-intersection-python
        buffered_geom_collection = geom_collection_valid.Buffer(0)

        # get intersection
        intersection = buffered_geom_collection.Intersection(zone_geom)
        if intersection is not None and intersection.GetArea() > 0:
            intersect_area = intersection.GetArea()
            print('{} has {} sq.m. of combustible land - {}% of its total area.'.format(zone_name,
                  intersect_area, 100 * intersect_area / zone_area_sqm))

    delta = datetime.now() - start_time
    print('Script took {} seconds to run.'.format(delta.seconds))


if __name__ == '__main__':
    # Usage:
    # advisory.calculate_combustible_land_area <fire_zones_shapefile_path> <fuel_types_geotiff_path>
    # 1. convert all input files to EPSG:3005
    transform_shapefile_to_epsg_3005(sys.argv[1], 'fire_zones_epsg_3005')
    transform_geotiff_to_epsg_3005(sys.argv[2], 'fuel_types_epsg_3005')
    # 2. polygonize the fuel types geotiff
    polygonize_geotiff('fuel_types_epsg_3005.tif', 'fuel_types_epsg_3005')
    # 3. calculate area of combustible fuel by zone
    calculate_combustible_area_by_fire_zone('fuel_types_epsg_3005.shp', 'fire_zones_epsg_3005.shp')
