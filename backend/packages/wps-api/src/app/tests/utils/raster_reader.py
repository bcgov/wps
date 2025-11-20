"""Helpers for reading gdal raster fixture files"""
from osgeo import gdal
import numpy

def read_raster_array(path: str) -> numpy.ndarray:
    """ Given a file path, read the raster data from the file and return as ndarray """
    source = gdal.Open(path, gdal.GA_ReadOnly)
    source_band = source.GetRasterBand(1)
    nodata_value = source_band.GetNoDataValue()
    source_data = source.ReadAsArray()
    source_data[source_data == nodata_value] = 0
    del source
    return source_data