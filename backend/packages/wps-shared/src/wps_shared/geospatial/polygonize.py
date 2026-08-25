"""Code for polygonizing a geotiff file."""

from contextlib import contextmanager
from typing import Generator

from osgeo import gdal, ogr, osr

from wps_shared.geospatial.wps_dataset import WPSDataset


@contextmanager
def polygonize_in_memory(geotiff_filename, layer, field) -> Generator[ogr.Layer, None, None]:
    """Given some tiff file, return a polygonized version of it, in memory, as an ogr layer."""
    with (
        WPSDataset(geotiff_filename) as source,
        source.with_array(source.get_valid_mask(), datatype=gdal.GDT_Byte) as mask,
    ):
        source_band = source.ds.GetRasterBand(1)
        # https://gdal.org/api/python/osgeo.osr.html#osgeo.osr.SpatialReference
        spatial_reference: osr.SpatialReference = source.ds.GetSpatialRef()

        # Create a memory OGR datasource to put results in.
        # https://gdal.org/drivers/vector/memory.html#vector-memory
        mem_drv: ogr.Driver = ogr.GetDriverByName("MEM")
        # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.DataSource
        dst_ds: ogr.DataSource = mem_drv.CreateDataSource("out")

        dst_layer: ogr.Layer = dst_ds.CreateLayer(layer, spatial_reference, ogr.wkbPolygon)
        field_name = ogr.FieldDefn(field, ogr.OFTInteger)
        field_name.SetWidth(24)
        dst_layer.CreateField(field_name)

        gdal.Polygonize(source_band, mask.ds.GetRasterBand(1), dst_layer, 0, [], callback=None)

        dst_ds.FlushCache()

    yield dst_layer
    del dst_ds, dst_layer
