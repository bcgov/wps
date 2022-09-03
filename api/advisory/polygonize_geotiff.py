import sys
from osgeo import gdal, ogr


def polygonize_geotiff(raster_source_filename, vector_dest_filename):
    """
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
    # TODO: would be nice to rename this field to "Fuel Type Id" - "Band 1" means nothing
    dest_field = dest_layer.GetLayerDefn().GetFieldIndex('Band 1')
    gdal.Polygonize(source_band, None, dest_layer, dest_field, [])

    return 'Polygonized {} to {}'.format(raster_source_filename, vector_dest_filename)


if __name__ == '__main__':
    if len(sys.argv != 2):
        print('Usage: advisory.polygonize_geotiff <raster_source_filepath> <vector_destination_filename>')
    resp = polygonize_geotiff(sys.argv[1], sys.argv[2])
    print(resp)
