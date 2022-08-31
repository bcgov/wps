""" Proof of concept, run classification on HFI GeoTiff
"""
import os
import sys
import numpy as np
from osgeo import gdal, ogr, osr


def categorize_combustible_fuels(source_path, target_path) -> any:
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

    # Remove any existing target file.
    if os.path.exists(target_path):
        os.remove(target_path)
    output_driver = gdal.GetDriverByName("GTiff")
    # Create an object with the same dimensions as the input, but with 8 bit unsigned values.
    target_tiff = output_driver.Create(target_path, xsize=source_band.XSize,
                                       ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
    # Set the geotransform to the same as the input.
    target_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
    # Set the projection to EPSG:3005 (BC Albers)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    target_tiff.SetProjection(srs.ExportToWkt())

    # # Write the classified data to the band.
    target_band = target_tiff.GetRasterBand(1)
    target_band.SetNoDataValue(0)
    target_band.WriteArray(classified)

    # # Important to make sure data is flushed to disk!
    target_tiff.FlushCache()

    print('\nClassified fuel type tiff written to {}\n'.format(target_path))

    # Explicit delete to make sure underlying resources are cleared up!
    del source_band
    del source_tiff
    del target_band
    # del target_tiff
    del output_driver

    return target_tiff


def rasterize_fire_zones(fire_zones_path):
    """
    Convert fire zones shapefile (which is collection of polygons) to a rasterized geotiff called
    'fire_zones_raster.tif'
    """
    fire_zones_source = gdal.Open(fire_zones_path, gdal.GA_ReadOnly)
    print('\n\n')
    print('Fire zones projection: {}'.format(fire_zones_source.GetProjection()))
    print('\n\n')
    pixel_size = 2000

    gdal.Rasterize('fire_zones_raster.tif', fire_zones_source, format='GTIFF',
                   xRes=778, yRes=683, pixel_size=pixel_size, noData=-10000, initValues=-10000)
    # , outputType=gdal.GDT_Byte, creationOptions=[
    #                'COMPRESS=DEFLATE'], noData=-10000, initValues=-10000, xRes=pixel_size, yRes=-pixel_size, allTouched=True, burnValues=1)

    print('Finished rasterizing fire zones.')


def reproject_shapefile_to_epsg_3005(shapefile_dir):
    """
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    input_dataset = driver.Open(shapefile_dir, 0)
    input_layer = input_dataset.GetLayer()
    input_spatial_ref = input_layer.GetSpatialRef()

    print(input_spatial_ref)

    output_spatial_ref = osr.SpatialReference()
    output_spatial_ref.ImportFromEPSG(3005)

    coords_transform = osr.CreateCoordinateTransformation(input_spatial_ref, output_spatial_ref)

    # create output layer
    output_shapefile = 'fire_zones_epsg_3005.shp'
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    output_dataset = driver.CreateDataSource(output_shapefile)
    output_layer = output_dataset.CreateLayer("epsg_3005", geom_type=ogr.wkbMultiPolygon)

    input_layer_defn = input_layer.GetLayerDefn()
    for i in range(input_layer_defn.GetFieldCount()):
        field_defn = input_layer_defn.GetFieldDefn(i)
        output_layer.CreateField(field_defn)

    output_layer_defn = output_layer.GetLayerDefn()

    # loop through input features
    input_feature = input_layer.GetNextFeature()
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
        input_feature = input_layer.GetNextFeature()

    # save and close shapefile
    input_dataset = None
    output_dataset = None

# def rasterize_shapefile(shapefile_dir):
#     """
#     """
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#     source_data = driver.Open(shapefile_dir, 0)
#     geotransform = source_data.GetSpatialRef()
#     print('\n\n{}\n\n'.format(geotransform))

#     # create output file
#     output = 'output.tif'
#     target_ds = gdal.GetDriverByName('GTiff').Create(output, x_res, y_res, 1, gdal.GDT_Byte)
#     target_ds.SetGeoTransform((x_min, pixel_width, 0, y_min, 0, pixel_width))
#     band = target_ds.GetRasterBand(1)
#     no_data_value = -10000
#     band.SetNoDataValue(no_data_value)
#     band.FlushCache()
#     gdal.RasterizeLayer(target_ds, [1], )

#     target_ds = None


def polygonize_combustible_fuels(combustible_fuels_tiff):
    """
    Converts combustible_fuels_tiff (as raster) to polygons, stored in
    POLYGONIZED_COMBUSTIBLE_FUELS.shp
    """
    combustible_fuels_band = combustible_fuels_tiff.GetRasterBand(1)

    dst_layername = "POLYGONIZED_COMBUSTIBLE_FUELS"
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dest_ds = driver.CreateDataSource(dst_layername + ".shp")
    dest_srs = ogr.osr.SpatialReference()
    dest_srs.ImportFromEPSG(3005)
    dest_layer = dest_ds.CreateLayer(dst_layername, geom_type=ogr.wkbPolygon, srs=dest_srs)

    return gdal.Polygonize(combustible_fuels_band, None, dest_layer, -1, [], callback=None)


def calculate_combustible_area_per_fire_zone(combustible_fuels_shapefile_dir, fire_zones_shapefile_dir):
    """
    Calculate the area of the combustible fuel types in each fire zone.
    """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    fire_zones_source = driver.Open(fire_zones_shapefile_dir, 0)

    if fire_zones_source is None:
        print('Could not open {}'.format(fire_zones_shapefile_dir))
    else:
        fire_zones_layer = fire_zones_source.GetLayer()
        # srs = osr.SpatialReference()
        # srs.ImportFromEPSG(3005)
        # fire_zones_source.SetProjection(srs.ExportToWkt())
        print('Fire zones projection {}'.format(fire_zones_layer.GetSpatialRef().ExportToWkt()))
        feature_count = fire_zones_layer.GetFeatureCount()
        print('Feature count: {}'.format(feature_count))

    combustible_fuels_source = driver.Open(combustible_fuels_shapefile_dir, 0)
    if combustible_fuels_source is None:
        print('Could not open {}'.format(combustible_fuels_shapefile_dir))
    else:
        combustible_fuels_layer = combustible_fuels_source.GetLayer()
        print('Combustible fuels feature count: {}'.format(combustible_fuels_layer.GetFeatureCount()))

    print('\nCombustible_fuels_layer projection {}\n'.format(combustible_fuels_layer.GetSpatialRef().ExportToWkt()))

    for zone_feature in fire_zones_layer:
        zone_geom = zone_feature.GetGeometryRef()
        zone_geom_clone = zone_geom.Clone()
        filtered_fuels = combustible_fuels_layer.SetSpatialFilter(zone_geom_clone)
        print('filtered_fuels count {}'.format(len(filtered_fuels)))
        if filtered_fuels is not None:
            for combustible_feature in filtered_fuels:
                print('{} features in combustible_fuels_layer for {}'.format(
                    filtered_fuels.GetFeatureCount(), zone_feature.GetField("MFFRZNNM")))
                combustible_fuel_geom = combustible_feature.GetGeometryRef()
                intersect = combustible_fuel_geom.Intersection(zone_geom)
                if intersect.Area() > 0:
                    print('{} has combustible area of {} of total area {} = {}%'.format(
                        zone_feature.GetField("MFFRZNNM"), intersect.Area(), zone_feature.GetField("AREA_SQM"),
                        100 * (intersect.Area() / zone_feature.GetField("AREA_SQM"))
                    ))
        else:
            print('No combustible fuels found for {} - bounds {}'.format(zone_feature.GetField('MFFRZNNM'),
                  zone_geom_clone.GetEnvelope()))


if __name__ == '__main__':
    # reproject_shapefile_to_epsg_3005(sys.argv[1])
    # categorized_fuels_tif = categorize_combustible_fuels(sys.argv[1], sys.argv[2])
    rasterize_fire_zones(sys.argv[1])
    # rasterize_shapefile(sys.argv[1])
    # polygonize_combustible_fuels(categorized_fuels_tif)
    # calculate_combustible_area_per_fire_zone(sys.argv[3], sys.argv[4])
