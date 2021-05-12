""" Take a tiff with one band, and split that band into 3 """
import struct
import numpy
from osgeo import gdal

inputfilename = '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/2018_ftl.tif'
outputfilename = '/home/sybrand/Workspace/wps/openshift/mapserver/docker/etc/mapserver/2018_ftl-3band.tif'

# read input file
raster_in = gdal.Open(inputfilename)
projection = raster_in.GetProjection()
geotransform = raster_in.GetGeoTransform()
band = raster_in.GetRasterBand(1)

print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))
print(f'band.XSize: {band.XSize}')
print(f'band.YSize: {band.YSize}')

# create output file
driver = gdal.GetDriverByName("GTiff")
outdata = driver.Create(outputfilename, band.XSize, band.YSize, 3, gdal.GDT_Byte)
outdata.SetProjection(projection)
outdata.SetGeoTransform(geotransform)

r_band = outdata.GetRasterBand(1)
r_band.SetColorInterpretation(gdal.GCI_RedBand)

g_band = outdata.GetRasterBand(2)
g_band.SetColorInterpretation(gdal.GCI_GreenBand)

b_band = outdata.GetRasterBand(3)
b_band.SetColorInterpretation(gdal.GCI_BlueBand)


for y in range(band.YSize):
    if y % 200 == 0:
        print(f'{y / band.YSize * 100}%')
    if band.DataType == gdal.GDT_Float32:
        buffer_type = gdal.GDT_Float32
    else:
        buffer_type = gdal.GDT_Int32
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=buffer_type)
    if buffer_type == gdal.GDT_Int32:
        array = struct.unpack('i' * band.XSize, scanline)
    else:
        array = struct.unpack('f' * band.XSize, scanline)

    r_array, g_array, b_array = [], [], []
    r_array.append([])
    g_array.append([])
    b_array.append([])
    for x in array:
        if buffer_type != gdal.GDT_Int32:
            # convert floating point to int - we don't care that much.
            x = int(x)
        r_array[0].append((x >> 16) & 0xff)
        g_array[0].append((x >> 8) & 0xff)
        b_array[0].append(x & 0xff)

    r_band.WriteArray(numpy.array(r_array), xoff=0, yoff=y)
    g_band.WriteArray(numpy.array(g_array), xoff=0, yoff=y)
    b_band.WriteArray(numpy.array(b_array), xoff=0, yoff=y)

outdata.FlushCache()

del raster_in
del outdata
