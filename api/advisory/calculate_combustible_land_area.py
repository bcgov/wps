""" Proof of concept, run classification on HFI GeoTiff
"""
import os
import sys
import numpy as np
from osgeo import gdal
import geojson


def categorize_combustible_fuels(source_path, target_path) -> any:
    """
    Given a source path of some GeoTIFF describing fuel types, classify the GeoTIFF according to whether
    the fuel type is combustible (1) or non-combustible (0), and save it to a new GeoTIFF.
    The output GeoTIFF will use 8 bit unsigned values.
    """
    # Read the source data.
    source_tiff = gdal.Open(source_path, gdal.GA_ReadOnly)
    print('******************************************')
    print('SOURCE TIFF DATA:')
    print('Projection: {}'.format(source_tiff.GetProjection()))
    print('Raster XSize x YSize: {} x {}'.format(source_tiff.RasterXSize, source_tiff.RasterYSize))
    print('Raster Count: {}'.format(source_tiff.RasterCount))
    source_band = source_tiff.GetRasterBand(1)
    source_band.ComputeStatistics(0)
    source_band.GetMetadata()
    print("[ NO DATA VALUE ]: {}".format(source_band.GetNoDataValue()))
    print("[ MIN ]: {}".format(source_band.GetMinimum()))
    print("[ MAX ]: {}".format(source_band.GetMaximum()))
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

    # Explicit delete to make sure underlying resources are cleared up!
    del source_band
    del source_tiff
    del target_band
    # del target_tiff
    del output_driver

    return target_tiff


def calculate_combustible_area_per_fire_zone(combustible_fuels_tiff, fire_zones_path):
    """
    Calculate the area of the combustible fuel types in each fire zone.
    """
    combustible_fuels_band = combustible_fuels_tiff.GetRasterBand(1)
    combustible_fuels_data = combustible_fuels_band.ReadAsArray()
    with open(fire_zones_path, 'r') as f:
        fire_zones = geojson.load(f)
    for feature in fire_zones['features']:
        # for each fire zone geometry, find the intersecting area of the combustible fuels.
        intersect = combustible_fuels_data.ST_Intersection(feature['geometry'])
        print('{} has combustible area of {} of total area {}'.format(
            feature['properties']['MOF_FIRE_ZONE_NAME'], intersect.ST_Area()))


if __name__ == '__main__':
    categorized_fuels_tif = categorize_combustible_fuels(sys.argv[1], sys.argv[2])
    calculate_combustible_area_per_fire_zone(categorized_fuels_tif, sys.argv[3])
