""" Take three different tiff files (DEM, aspect and slope) - and squeeze all the data into one
tiff file.

Elevation:
Highest peak in BC is 4671M, so we can safely use 13 bits for 1m elevation

13 bits - elevation at 1m intervals (max 8192)
12 bits - elevation at 2m intervals (max 4096)
11 bits - elevation at 3m intervals (max 2048)
8 bits  - elevation at 20m intervals (max 255)

Aspect - if we limit it to 4 directions, then:
1 bits - indicate validity
3 bits - 8 directions

Slope - in degrees - lots of space, we take 7 bits 
7 bits


Elevation, 1m intervals: 13 bits
Aspect, validity + 8 directions: 4 bits
Slope, up to 128 degree: 7 bits
"""
import struct
import numpy
from osgeo import gdal


def check_project_geotransform_match(dataset_a: gdal.Dataset, dataset_b: gdal.Dataset):
    """ Check that datasets have the same projection and transformation. """
    if dataset_a.GetProjection() != dataset_b.GetProjection():
        raise Exception('non matching projection')
    if dataset_a.GetGeoTransform() != dataset_b.GetGeoTransform():
        raise Exception('non matching geotransform')


def check_band_match(band_a, band_b):
    """ Check that the bands have the same size """
    if band_a.XSize != band_b.XSize:
        raise Exception('non matching band size')
    if band_a.YSize != band_b.YSize:
        raise Exception('non matching band size')


def get_int32_array(band, y: int):
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Int32)
    return struct.unpack('i' * band.XSize, scanline)


def get_float32_array(band, y: int):
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Float32)
    return struct.unpack('f' * band.XSize, scanline)


def main():
    # elevation in meters
    elevation_file = '92p-utm-elevation.tif'
    # aspect in degrees
    aspect_file = '92p-utm-aspect.tif'
    # slope in percentage
    # https://gdal.org/programs/gdaldem.html
    # percentage: gdaldem slope 92p-utm-elevation.dem 92p-utm-slope-percentage.tif -of GTiff -b 1 -s 1.0 -p
    # degrees: gdaldem slope 92p-utm-elevation.dem 92p-utm-slope-degree.tif -of GTiff -b 1 -s 1.0
    slope_file = '92p-utm-slope-degree.tif'

    # outputfilename = '92p-utm-eas-3band.tif'
    outputfilename = '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/92p-utm-eas-3band.tif'

    # read input file
    elevation_ds = gdal.Open(elevation_file)
    aspect_ds = gdal.Open(aspect_file)
    slope_ds = gdal.Open(slope_file)
    try:

        # compare projections and transformations - have to be the same!
        check_project_geotransform_match(elevation_ds, aspect_ds)
        check_project_geotransform_match(elevation_ds, slope_ds)

        projection = elevation_ds.GetProjection()
        geotransform = elevation_ds.GetGeoTransform()

        elevation_band = elevation_ds.GetRasterBand(1)
        aspect_band = aspect_ds.GetRasterBand(1)
        slope_band = slope_ds.GetRasterBand(1)

        check_band_match(elevation_band, aspect_band)
        check_band_match(elevation_band, slope_band)

        print("Elevation Band Type={}".format(gdal.GetDataTypeName(elevation_band.DataType)))
        print("Aspect Band Type={}".format(gdal.GetDataTypeName(aspect_band.DataType)))
        print("Slope Band Type={}".format(gdal.GetDataTypeName(slope_band.DataType)))
        print(f'band.XSize: {elevation_band.XSize}')
        print(f'band.YSize: {elevation_band.YSize}')

        # create output file
        driver = gdal.GetDriverByName("GTiff")
        outdata = driver.Create(outputfilename, elevation_band.XSize, elevation_band.YSize, 3, gdal.GDT_Byte)
        try:
            outdata.SetProjection(projection)
            outdata.SetGeoTransform(geotransform)

            r_band = outdata.GetRasterBand(1)
            r_band.SetColorInterpretation(gdal.GCI_RedBand)

            g_band = outdata.GetRasterBand(2)
            g_band.SetColorInterpretation(gdal.GCI_GreenBand)

            b_band = outdata.GetRasterBand(3)
            b_band.SetColorInterpretation(gdal.GCI_BlueBand)

            r_rows = []
            g_rows = []
            b_rows = []

            aspects = 0

            for y in range(elevation_band.YSize):
                if y % 200 == 0:
                    print(f'{y / elevation_band.YSize * 100}% done')

                elevation_array = get_int32_array(elevation_band, y)
                aspect_array = get_float32_array(aspect_band, y)
                slope_array = get_float32_array(slope_band, y)

                r_array, g_array, b_array = [], [], []

                for elevation, aspect, slope in zip(elevation_array, aspect_array, slope_array):
                    # print(f'elevation:{elevation}')
                    # shift elevation left 11 bits
                    value = (elevation << 11)
                    # is the aspect valid? (flat ground doesn't have an aspect!)
                    valid_aspect = aspect >= 0 and aspect <= 360
                    value = value | valid_aspect << 10
                    # simplify the aspect
                    aspect = int(aspect / 45) & 0x7
                    value = value | aspect << 7
                    # 7 bits left for the slope
                    if slope < 0 or slope > 360:
                        # we just assume 0 for the slope if there is none.
                        slope = 0
                    value = value | int(slope) & 0x7F

                    # print(f'value:{value}'')

                    r_array.append((value >> 16) & 0xFF)
                    g_array.append((value >> 8) & 0xFF)
                    b_array.append(value & 0xFF)

                r_rows.append(r_array)
                g_rows.append(g_array)
                b_rows.append(b_array)

            r_band.WriteArray(numpy.array(r_rows))
            g_band.WriteArray(numpy.array(g_rows))
            b_band.WriteArray(numpy.array(b_rows))

            outdata.FlushCache()
        finally:
            del outdata

    finally:
        del elevation_ds
        del aspect_ds
        del slope_ds


main()
