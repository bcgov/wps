""" Module for generating c-haines charts from grib files.
Contains some common code.
"""

import gdal


class GDALData():
    """ Assumes all three the grib files are using the same projection and transformation.
    """

    def __init__(self, grib_tmp_700: gdal.Dataset, grib_tmp_850: gdal.Dataset, grib_dew_850: gdal.Dataset):
        self.grib_tmp_700: gdal.Dataset = grib_tmp_700
        self.grib_tmp_850: gdal.Dataset = grib_tmp_850
        self.grib_dew_850: gdal.Dataset = grib_dew_850
