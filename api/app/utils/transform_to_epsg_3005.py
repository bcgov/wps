import sys
import os
from osgeo import osr, gdal, ogr


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
    if new_filename[-3:] != '.shp':
        new_filename += '.shp'
    output_shapefile = new_filename
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

    del source_data, output_dataset, coords_transform

    return 'Transformed shapefile written to {}'.format(new_filename)


def transform_geotiff_to_epsg_3005(source_file, new_filename):
    """
    Transforms coordinates in source_file geotiff to EPSG:3005 (BC Albers),
    writes to newly created geotiff called <new_filename>.tif
    """
    source_data = gdal.Open(source_file, gdal.GA_ReadOnly)
    if new_filename[-3:] != '.tif':
        new_filename += '.tif'
    gdal.Warp(new_filename, source_data, dstSRS='EPSG:3005')

    # close file so it is written to disk
    source_data = None

    del source_data

    return 'Transformed geotiff written to {}'.format(new_filename)


def transform_file(filepath, new_filename):
    if filepath[-3:] == '.tif':
        transform_geotiff_to_epsg_3005(filepath, new_filename)
    elif filepath[-3:] == '.shp':
        transform_shapefile_to_epsg_3005(filepath, new_filename)
    else:
        return 'Invalid file format.'


if __name__ == '__main__':
    if len(sys.argv != 2):
        print('Usage: advisory.transform_to_epsg_3005 <source_filepath> <destination_filename>')
    resp = transform_file(sys.argv[1], sys.argv[2])
    print(resp)
