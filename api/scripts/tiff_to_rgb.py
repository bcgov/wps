""" Take a tiff with one band, and split that band into 3 """
import struct
import numpy
from osgeo import gdal

# read input file
raster_in = gdal.Open('92p-utm-elevation.tif')
projection = raster_in.GetProjection()
geotransform = raster_in.GetGeoTransform()
band = raster_in.GetRasterBand(1)

print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))
print(f'band.XSize: {band.XSize}')
print(f'band.YSize: {band.YSize}')

# create output file
driver = gdal.GetDriverByName("GTiff")
outdata = driver.Create('92p-utm-elevation-3band.tif', band.XSize, band.YSize, 3, gdal.GDT_Byte)
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

for y in range(band.YSize):
    if y % 200 == 0:
        print(f'{y / band.XSize * 100}%')
    scanline = band.ReadRaster(xoff=0, yoff=y,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Int32)
    array = struct.unpack('i' * band.XSize, scanline)

    r_array, g_array, b_array = [], [], []
    for x in array:
        r_array.append((x >> 16) & 0xff)
        g_array.append((x >> 8) & 0xff)
        b_array.append(x & 0xff)
    r_rows.append(r_array)
    g_rows.append(g_array)
    b_rows.append(b_array)

r_band.WriteArray(numpy.array(r_rows))
g_band.WriteArray(numpy.array(g_rows))
b_band.WriteArray(numpy.array(b_rows))

outdata.FlushCache()

del raster_in
del outdata
