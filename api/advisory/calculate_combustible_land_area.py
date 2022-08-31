import os
from osgeo import gdal, osr, ogr


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

    print(input_spatial_ref)

    output_spatial_ref = osr.SpatialReference()
    output_spatial_ref.ImportFromEPSG(3005)

    coords_transform = osr.CreateCoordinateTransformation(input_spatial_ref, output_spatial_ref)

    # create output layer
    output_shapefile = new_filename + '.shp'
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    output_dataset = driver.CreateDataSource(output_shapefile)
    output_layer = output_dataset.CreateLayer("epsg_3005", geom_type=ogr.wkbMultiPolygon)

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
    return


def transform_geotiff_to_epsg_3005(source_file, new_filename):
    """
    Transforms coordinates in source_file geotiff to EPSG:3005 (BC Albers),
    writes to newly created geotiff called <new_filename>.tif
    """
    source_data = gdal.Open(source_file, gdal.GA_ReadOnly)
    warp = gdal.Warp(new_filename + '.tif', source_data, dstSRS='EPSG:3005')

    # close file so it is written to disk
    warp, source_data = None

    print('Transformed geotiff written to {}'.format(new_filename + '.tif'))

    del source_data, warp
    return


def rasterize_shapefile(vector_source_filename, raster_dest_filename):
    """
    Ingests the file <vector_source_filename>, creates new file called
    <raster_dest_filename>, and inputs rasterized contents of source file
    into destination file.
    """
    source_data = gdal.Open(vector_source_filename, gdal.GA_ReadOnly)
    # ulx, uly is coordinates of Upper Left corner
    ulx, xres, xskew, uly, yskew, yres = source_data.GetGeoTransform()
    # lrx, lrx is coordinates of Lower Right corner
    lrx = ulx + (source_data.RasterXSize * xres)
    lry = uly + (source_data.RasterYSize * yres)

    output_file = raster_dest_filename + '.tif'
    dest_data = gdal.GetDriverByName('GTiff').Create(output_file, xres, yres, 1, gdal.GDT_Byte)
    dest_data.SetGeoTransform((ulx, xres, xskew, uly, yskew, yres))
    band = dest_data.GetRasterBand(1)
    no_data_value = -10000
    band.SetNoDataValue(no_data_value)
    band.FlushCache()

    gdal.RasterizeLayer(dest_data, source_data)

    # close files
    dest_data, source_data = None
    del dest_data, source_data
    return


def classify_combustible_fuels():
    return


def calculate_combustible_area_by_fire_zone():
    return


if __name__ == '__main__':
    # 1. convert all input files to EPSG:3005
    # 2. rasterize fire zones shapefile
    # 3. convert fuel types raster into bitmask of combustible/not
    # 4. calculate area of combustible fuel by zone
