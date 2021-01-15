""" Code for generating c-haines charts from grib files.

Process:
- Open grib files.
- Calculate c-haines in in memory raster layer.
- Polygonize the raster to a geojson data source.
NEXT:
- Load geojson, iterating through and saving it in the database.
- Simplify polygons.
- Load geojson from API and display in web map.
- Download all grib files for model run.
"""
from typing import Final
import json
import logging
import struct
import numpy
import gdal
import ogr
from shapely.geometry import shape
from app import configure_logging
from app.db.models import CHainesPoly
import app.db.database

logger = logging.getLogger(__name__)


def read_scanline(band, yoff):
    """ Read a band scanline, returning an array of values. """
    scanline = band.ReadRaster(xoff=0, yoff=yoff,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Float32)
    return struct.unpack('f' * band.XSize, scanline)


def calculate_c_haines_index(t700: float, t850: float, td850: float):
    """ Given temperature and dew points values, calculate c-haines.  """
    # pylint: disable=invalid-name

    # Temperature depression term (this indicates atmospheric instability).
    # Temperature at 850mb - Temperature at 700mb.
    ca = (t850-t700)/2-2
    # Dew point depression term (this indicates how dry the air is).
    # Temperature at 850mb - Dew point at 850mb.
    cb = (t850-td850)/3-1

    # This part limits the extent to which dry air is able to affect the overall index.
    # If there is very dry air (big difference between dew point temperature and temperature),
    # we want to limit to overall effect on the index, since if there's no atmospheric
    # instability, that dry air isn't going anywhere.
    if cb > 9:
        cb = 9
    elif cb > 5:
        cb = 5 + (cb-5)/2
    ch = ca + cb

    return ch


def calculate_c_haines_data(
        grib_tmp_700: gdal.Dataset, grib_tmp_850: gdal.Dataset, grib_dew_850: gdal.Dataset):
    """ Given grib data sets for temperature and dew point, create array of data containing
    c-haines indices and mask """
    logger.info('calculting c-haines data...')

    # Load the raster data.
    tmp_850_raster_band = grib_tmp_850.GetRasterBand(1)
    tmp_700_raster_band = grib_tmp_700.GetRasterBand(1)
    dew_850_raster_band = grib_dew_850.GetRasterBand(1)

    c_haines_data: Final = []
    mask_data: Final = []

    # Assume they're all using the same number of rows/cols.
    rows: Final = tmp_850_raster_band.YSize
    cols: Final = tmp_850_raster_band.XSize

    # Iterate through rows.
    for row_index in range(rows):
        # Read the scanlines.
        row_tmp_700 = read_scanline(tmp_700_raster_band, row_index)
        row_tmp_850 = read_scanline(tmp_850_raster_band, row_index)
        row_dew_850 = read_scanline(dew_850_raster_band, row_index)

        chaines_row = []
        mask_row = []
        # TODO: Look at using numpy to iterate through this faster.
        # Iterate through values in row.
        for t700, t850, td850 in zip(row_tmp_700, row_tmp_850, row_dew_850):
            # pylint: disable=invalid-name
            ch = calculate_c_haines_index(t700, t850, td850)
            # We're not interested in such finely grained results, so
            # we bucket them together as such:
            # 0 - 7 (Very low, low)
            if ch < 7:
                level = 0
            # 7 - 9 (Moderate)
            elif ch < 9:
                level = 1
            # 9 - 11 (High to very high)
            elif ch < 11:
                level = 2
            # 11 and up (Very high)
            else:
                level = 3
            chaines_row.append(level)

            # We ignore level 0
            if level == 0:
                mask_row.append(0)
            else:
                mask_row.append(1)

        c_haines_data.append(chaines_row)
        mask_data.append(mask_row)

    # TODO: look at creating numpy arrays from the get go
    return numpy.array(c_haines_data), numpy.array(mask_data), rows, cols


def save_data_as_tiff(
        c_haines_data: numpy.ndarray,
        target_filename: str,
        rows: int,
        cols: int,
        source_projection,
        source_geotransform):
    logger.info('saving output as tiff %s...', target_filename)
    driver = gdal.GetDriverByName("GTiff")
    outdata = driver.Create(target_filename, cols, rows, 1, gdal.GDT_Byte)
    outdata.SetProjection(source_projection)
    outdata.SetGeoTransform(source_geotransform)

    colors = gdal.ColorTable()
    # white
    colors.SetColorEntry(0, (255, 255, 255))
    # yellow
    colors.SetColorEntry(1, (255, 255, 0))
    # red
    colors.SetColorEntry(2, (255, 0, 0))
    # purple
    colors.SetColorEntry(3, (128, 0, 128))

    band = outdata.GetRasterBand(1)
    band.SetRasterColorTable(colors)
    band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)

    band.WriteArray(numpy.array(c_haines_data))
    outdata.FlushCache()


# def convert_to_polygon(ch_data: numpy.ndarray,
#                        mask_data: numpy.ndarray,
#                        projection,
#                        geotransform,
#                        rows: int,
#                        cols: int):
#     """ This doesn't work """

#     mem_driver = gdal.GetDriverByName('MEM')

#     # Create data band.
#     data_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     data_ds.SetProjection(projection)
#     data_ds.SetGeoTransform(geotransform)
#     data_band = data_ds.GetRasterBand(1)
#     data_band.WriteArray(ch_data)

#     # Create mask band.
#     mask_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     mask_ds.SetProjection(projection)
#     mask_ds.SetGeoTransform(geotransform)
#     mask_band = mask_ds.GetRasterBand(1)
#     mask_band.WriteArray(mask_data)

#     # Flush.
#     data_ds.FlushCache()
#     mask_ds.FlushCache()

#     # Create polygon data source
#     # polygon_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     # ogr_mem_driver = ogr.GetDriverByName('MEMORY')
#     polygon_ds = mem_driver.CreateDataSource('memdata')
#     dst_layer = polygon_ds.CreateLayer('C-Haines', srs=None)
#     field_name = ogr.FieldDefn("index", ogr.OFTInteger)
#     field_name.SetWidth(24)
#     dst_layer.CreateField(field_name)
#     # Turn the rasters into polygons
#     gdal.Polygonize(data_band, mask_band, dst_layer, 0, [], callback=None)
#     polygon_ds.FlushCache()

#     del data_ds, mask_ds

#     return dst_layer


def save_data_as_geojson(
        ch_data: numpy.ndarray,
        mask_data: numpy.ndarray,
        projection,
        geotransform,
        rows: int,
        cols: int,
        target_filename: str):
    """ Save data as geojson polygon """
    logger.info('saving output as geojson %s...', target_filename)

    mem_driver = gdal.GetDriverByName('MEM')

    # Create data band.
    data_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    data_ds.SetProjection(projection)
    data_ds.SetGeoTransform(geotransform)
    data_band = data_ds.GetRasterBand(1)
    data_band.WriteArray(ch_data)

    # Create mask band.
    mask_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    mask_ds.SetProjection(projection)
    mask_ds.SetGeoTransform(geotransform)
    mask_band = mask_ds.GetRasterBand(1)
    mask_band.WriteArray(mask_data)

    # Flush.
    data_ds.FlushCache()
    mask_ds.FlushCache()

    # Save as geojson
    geojson_driver = ogr.GetDriverByName('GeoJSON')
    dst_ds = geojson_driver.CreateDataSource('c-haines.geojson')
    dst_layer = dst_ds.CreateLayer('C-Haines', srs=None)
    field_name = ogr.FieldDefn("severity", ogr.OFTInteger)
    field_name.SetWidth(24)
    dst_layer.CreateField(field_name)
    # Turn the rasters into polygons
    gdal.Polygonize(data_band, mask_band, dst_layer, 0, [], callback=None)
    dst_ds.FlushCache()

    # Explicitly clean up (is this needed?)
    del dst_ds, data_ds, mask_ds


def save_geojson_to_database(filename: str):
    """ Open geojson file, iterate through features, saving them into the
    databse.
    """
    logger.info('saving geojson %s to database...', filename)
    session = app.db.database.get_write_session()
    # Open the geojson file.
    with open(filename) as file:
        data = json.load(file)
    # Convert each feature into a shapely geometry and save to database.
    for feature in data['features']:
        geometry = shape(feature['geometry'])
        polygon = CHainesPoly(geom=geometry.wkt, severity=feature['properties']['severity'])
        session.add(polygon)
    session.commit()
    # TODO: simplify geometry: https://shapely.readthedocs.io/en/stable/manual.html#object.simplify


def thing(filename_tmp_700: str, filename_tmp_850: str, filename_dew_850: str):
    # Open the grib files.
    grib_tmp_700 = gdal.Open(filename_tmp_700, gdal.GA_ReadOnly)
    grib_tmp_850 = gdal.Open(filename_tmp_850, gdal.GA_ReadOnly)
    grib_dew_850 = gdal.Open(filename_dew_850, gdal.GA_ReadOnly)

    # Assume they're all using the same projection and transformation.
    projection = grib_tmp_850.GetProjection()
    geotransform = grib_tmp_850.GetGeoTransform()

    c_haines_data, mask_data, rows, cols = calculate_c_haines_data(grib_tmp_700, grib_tmp_850, grib_dew_850)

    # Expictly release the grib files - they take a lot of memory. (Is this needed?)
    del grib_tmp_700, grib_tmp_850, grib_dew_850

    # Save to tiff (for easy debugging)
    save_data_as_tiff(
        c_haines_data, 'c-haines.tiff', rows, cols, projection, geotransform)

    # Save to geojson
    save_data_as_geojson(
        c_haines_data,
        mask_data,
        projection,
        geotransform,
        rows,
        cols,
        'c-haines.geojson')

    save_geojson_to_database('c-haines.geojson')


def main():
    filename_tmp_700 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_TMP_ISBL_700_latlon.15x.15_2020122200_P000.grib2'
    filename_tmp_850 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_TMP_ISBL_850_latlon.15x.15_2020122200_P000.grib2'
    filename_dew_850 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2020122200_P000.grib2'

    thing(filename_tmp_700, filename_tmp_850, filename_dew_850)


if __name__ == "__main__":
    configure_logging()
    main()
