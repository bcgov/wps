import os
import sys
from osgeo import gdal, osr, ogr
import numpy as np


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


def rasterize_shapefile(vector_source_filename, raster_dest_filename):
    """
    Ingests the file <vector_source_filename>, creates new file called
    <raster_dest_filename>.tif, and inputs rasterized contents of source file
    into destination file.
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    source_data = driver.Open(vector_source_filename, gdal.GA_ReadOnly)
    if source_data is None:
        print('Could not open file {}'.format(vector_source_filename))
        return

    source_layer = source_data.GetLayer()
    # source_spatial_ref = source_layer.GetSpatialRef()

    output_file = raster_dest_filename + '.tif'
    dest_data = gdal.GetDriverByName('GTiff').Create(output_file, 791, 694, 1, gdal.GDT_Byte)
    band = dest_data.GetRasterBand(1)
    no_data_value = -10000
    band.SetNoDataValue(no_data_value)
    band.FlushCache()

    gdal.RasterizeLayer(dest_data, [1], source_layer)

    # close files
    dest_data, source_data = None, None
    return


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


def classify_combustible_fuels(source_path, target_path):
    """
    Given a source path of some GeoTIFF describing fuel types, classify the GeoTIFF according to whether
    the fuel type is combustible (1) or non-combustible (0), and save it to a new GeoTIFF.
    The output GeoTIFF will use 8 bit unsigned values.
    """
    # Read the source data.
    source_tiff = gdal.Open(source_path, gdal.GA_ReadOnly)
    print('******************************************')
    print('COMBUSTIBLE FUELS SOURCE TIFF DATA:')
    print('Projection: {}'.format(source_tiff.GetProjection()))
    print('Raster XSize x YSize: {} x {}'.format(source_tiff.RasterXSize, source_tiff.RasterYSize))
    print('Raster Count: {}'.format(source_tiff.RasterCount))
    source_band = source_tiff.GetRasterBand(1)
    source_band.ComputeStatistics(0)
    source_band.GetMetadata()
    print("[ NO DATA VALUE ]: {}".format(source_band.GetNoDataValue()))
    print("[ MIN ]: {}".format(source_band.GetMinimum()))
    print("[ MAX ]: {}".format(source_band.GetMaximum()))
    ulx, xres, xskew, uly, yskew, yres = source_tiff.GetGeoTransform()
    print(ulx, xres, xskew, uly, yskew, yres)
    lrx = ulx + (source_tiff.RasterXSize * xres)
    lry = uly + (source_tiff.RasterYSize * yres)
    print("Upper left corner {}, {}. Lower right corner {}, {}.".format(ulx, uly, lrx, lry))
    print('******************************************')

    source_data = source_band.ReadAsArray()
    # Classify the data.
    # Null values are encoded in source_data as -10000.
    # Non-fuel types are encoded as one of 99, 100, 102, 103 (there is no 101).
    classified = np.where(source_data == -10000, 0, source_data)
    classified = np.where((classified == 99) | (classified == 100) | (
        classified == 102) | (classified == 103), 0, classified)
    # The rest of the fuel types are combustible.
    classified = np.where(classified > 0, 1, classified)

    target_path += '.tif'

    # Remove any existing target file.
    if os.path.exists(target_path):
        os.remove(target_path)
    output_driver = gdal.GetDriverByName("GTiff")
    # Create an object with the same dimensions as the input, but with 8 bit unsigned values.
    target_tiff = output_driver.Create(target_path, xsize=source_band.XSize,
                                       ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
    # Set the geotransform and projection to the same as the input.
    target_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
    target_tiff.SetProjection(source_tiff.GetProjection())

    # # Write the classified data to the band.
    target_band = target_tiff.GetRasterBand(1)
    target_band.SetNoDataValue(0)
    target_band.WriteArray(classified)

    # # Important to make sure data is flushed to disk!
    target_tiff.FlushCache()

    print('\nClassified fuel type tiff written to {}\n'.format(target_path))

    # Save and close geotiff files
    source_tiff, target_tiff = None, None

    # Explicit delete to make sure underlying resources are cleared up!
    del source_band
    del source_tiff
    del target_band
    del target_tiff
    del output_driver

    return


def calculate_combustible_area_by_fire_zone(fuel_types_vector_filename, fire_zones_vector_filename):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    fuel_types = driver.Open(fuel_types_vector_filename, gdal.GA_ReadOnly)
    fuel_types_layer = fuel_types.GetLayer()
    fire_zones = driver.Open(fire_zones_vector_filename, gdal.GA_ReadOnly)
    fire_zones_layer = fire_zones.GetLayer()

    print('Analyzing {} fire zones in {}'.format(fire_zones_layer.GetFeatureCount(), fire_zones_vector_filename))
    print('Analyzing {} fuel type polygons in {}'.format(fuel_types_layer.GetFeatureCount(), fuel_types_vector_filename))

    # for feature in fire_zones_layer:
    #     zone_name = feature.GetField('MFFRZNNM')
    #     zone_area_sqm = feature.GetField('AREA_SQM')
    #     print('{}: {} sq.m.'.format(zone_name, zone_area_sqm))
    #     zone_geom = feature.geometry()

    for feature in fuel_types_layer:
        print('Feature Metadata Dict: {}'.format(feature.items()))

    return


if __name__ == '__main__':
    # Usage:
    # advisory.calculate_combustible_land_area <fire_zones_shapefile_path> <fuel_types_geotiff_path>
    # 1. convert all input files to EPSG:3005
    # transform_shapefile_to_epsg_3005(sys.argv[1], 'fire_zones_epsg_3005')
    # transform_geotiff_to_epsg_3005(sys.argv[2], 'fuel_types_epsg_3005')
    # 2. rasterize fire zones shapefile
    # rasterize_shapefile('fire_zones_epsg_3005.shp', 'fire_zones_epsg_3005')

    # rasterizing was painful. Let's try polygonizing the fuel types geotiff instead
    # polygonize_geotiff('fuel_types_epsg_3005.tif', 'fuel_types_epsg_3005')

    # 3. convert fuel types raster into bitmask of combustible/not
    # classify_combustible_fuels('fuel_types_epsg_3005.tif', 'combustible_fuels_epsg_3005')
    # 4. calculate area of combustible fuel by zone
    calculate_combustible_area_by_fire_zone('fuel_types_epsg_3005.shp', 'fire_zones_epsg_3005.shp')
