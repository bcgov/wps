""" Code for polygonizing a geotiff file. """
from contextlib import contextmanager
from typing import Tuple
from osgeo import gdal, ogr, osr
import numpy as np


def _create_in_memory_band(data: np.ndarray, cols, rows, projection, geotransform):
    """ Create an in memory data band to represent a single raster layer.
    See https://gdal.org/user/raster_data_model.html#raster-band for a complete
    description of what a raster band is.
    """
    mem_driver = gdal.GetDriverByName('MEM')

    dataset = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    dataset.SetProjection(projection)
    dataset.SetGeoTransform(geotransform)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)

    return dataset, band


@contextmanager
def polygonize_in_memory(geotiff_filename) -> Tuple[ogr.DataSource, ogr.Layer]:
    """  Given some tiff file, return a polygonized version of it, in memory, as an ogr layer. """
    source: gdal.Dataset = gdal.Open(geotiff_filename, gdal.GA_ReadOnly)

    source_band = source.GetRasterBand(1)
    source_data = source.ReadAsArray()
    # https://gdal.org/api/python/osgeo.osr.html#osgeo.osr.SpatialReference
    spatial_reference: osr.SpatialReference = source.GetSpatialRef()

    # generate mask data
    mask_data = np.where(source_data == 0, False, True)
    mask_ds, mask_band = _create_in_memory_band(
        mask_data, source_band.XSize, source_band.YSize, source.GetProjection(),
        source.GetGeoTransform())

    # Create a memory OGR datasource to put results in.
    # https://gdal.org/drivers/vector/memory.html#vector-memory
    mem_drv: ogr.Driver = ogr.GetDriverByName("Memory")
    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.DataSource
    dst_ds: ogr.DataSource = mem_drv.CreateDataSource("out")

    dst_layer: ogr.Layer = dst_ds.CreateLayer("hfi", spatial_reference, ogr.wkbPolygon)
    field_name = ogr.FieldDefn("hfi", ogr.OFTInteger)
    field_name.SetWidth(24)
    dst_layer.CreateField(field_name)

    gdal.Polygonize(source_band, mask_band, dst_layer, 0, [], callback=None)

    dst_ds.FlushCache()
    del source, mask_band, mask_ds
    yield dst_layer
    del dst_ds, dst_layer


def polygonize_geotiff_to_shapefile(raster_source_filename, vector_dest_filename):
    """
    TODO: Automate this.
    At the moment this function isn't used as part of any automated process, 
    but has been used to manually convert the fuel type layer tiff to a shapefile,
    which then gets manually uploaded to our S3 bucket.

    Ingests the file <raster_source_filename>, creates new file called
    <vector_dest_filename>.shp, and inserts polygonized contents of source
    file into destination file.
    """
    if raster_source_filename[-3:] != '.tif':
        return '{} is an invalid file format for raster source'.format(raster_source_filename)
    if vector_dest_filename[-3:] != '.shp':
        vector_dest_filename += '.shp'

    source_data = gdal.Open(raster_source_filename, gdal.GA_ReadOnly)
    source_band = source_data.GetRasterBand(1)
    value = ogr.FieldDefn('Band 1', ogr.OFTInteger)
    print('{} raster count: {}'.format(raster_source_filename, source_data.RasterCount))

    driver = ogr.GetDriverByName("ESRI Shapefile")
    destination = driver.CreateDataSource(vector_dest_filename)
    dest_srs = ogr.osr.SpatialReference()
    dest_srs.ImportFromEPSG(3005)
    dest_layer = destination.CreateLayer(vector_dest_filename, geom_type=ogr.wkbPolygon, srs=dest_srs)
    dest_layer.CreateField(value)
    # 'Band 1' is the field name on the layer for Fuel Type ID
    dest_field = dest_layer.GetLayerDefn().GetFieldIndex('Band 1')
    gdal.Polygonize(source_band, None, dest_layer, dest_field, [])

    return 'Polygonized {} to {}'.format(raster_source_filename, vector_dest_filename)
