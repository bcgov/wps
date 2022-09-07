from osgeo import gdal, ogr, osr
from typing import Tuple, Any
import os
import json
import numpy as np
import tempfile


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


def polygonize(geotiff_filename) -> Tuple[ogr.DataSource, ogr.Layer]:
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
    return dst_ds, dst_layer

    # # Create a GeoJSON layer.
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     temp_filename = os.path.join(temp_dir, 'temp.geojson')
    #     geojson_driver = ogr.GetDriverByName('GeoJSON')
    #     dst_ds = geojson_driver.CreateDataSource(temp_filename)

    #     # HFI Layer
    #     dst_layer = dst_ds.CreateLayer('hfi')
    #     field_name = ogr.FieldDefn("hfi", ogr.OFTInteger)
    #     field_name.SetWidth(24)
    #     dst_layer.CreateField(field_name)

    #     # Turn the rasters into polygons.
    #     gdal.Polygonize(band, mask_band, dst_layer, 0, [], callback=None)

    #     # Ensure that all data in the target dataset is written to disk.
    #     dst_ds.FlushCache()
    #     # Explicitly clean up (is this needed?)
    #     del dst_ds, mask_band, mask_ds

    #     with open(temp_filename, encoding="utf-8") as source_file:
    #         geojson_data = json.load(source_file)

    # return geojson_data
