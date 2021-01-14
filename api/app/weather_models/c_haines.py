from typing import Final
import logging
import struct
import numpy
import gdal
from app import configure_logging

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

    # temperature depression term
    ca = (t850-t700)/2-2
    # dew point depression term
    cb = (t850-td850)/3-1

    # NOTE: this part doesn't make sense to me, source documentation says:
    # If(CB > 9) then CB = 9; If(CB > 5) then CB = 5+(CB-5)/2
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

    return c_haines_data, mask_data, rows, cols


def save_data_as_tiff(c_haines_data: [], target_filename: str, rows: int, cols: int, source_projection, source_geotransform):
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


def thing(filename_tmp_700: str, filename_tmp_850: str, filename_dew_850: str):
    # Open the grib files.
    grib_tmp_700 = gdal.Open(filename_tmp_700, gdal.GA_ReadOnly)
    grib_tmp_850 = gdal.Open(filename_tmp_850, gdal.GA_ReadOnly)
    grib_dew_850 = gdal.Open(filename_dew_850, gdal.GA_ReadOnly)

    # Assume they're all using the same projection and transformation.
    projection = grib_tmp_850.GetProjection()
    geotransform = grib_tmp_850.GetGeoTransform()

    c_haines_data, mask_data, rows, cols = calculate_c_haines_data(grib_tmp_700, grib_tmp_850, grib_dew_850)
    save_data_as_tiff(c_haines_data, 'out.tiff', rows, cols, projection, geotransform)

    # Expictly release the grib files - they take a lot of memory.
    del grib_tmp_700
    del grib_tmp_850
    del grib_dew_850


def main():
    filename_tmp_700 = 'scripts/CMC_glb_TMP_ISBL_700_latlon.15x.15_2020122200_P000.grib2'
    filename_tmp_850 = 'scripts/CMC_glb_TMP_ISBL_850_latlon.15x.15_2020122200_P000.grib2'
    filename_dew_850 = 'scripts/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2020122200_P000.grib2'

    thing(filename_tmp_700, filename_tmp_850, filename_dew_850)


if __name__ == "__main__":
    configure_logging()
    main()
