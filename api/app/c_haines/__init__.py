""" Module for generating c-haines charts from grib files.
Contains some common code.
"""
from enum import Enum
from osgeo import gdal


class GDALData():
    """ Assumes all three the grib files are using the same projection and transformation.
    """

    def __init__(self, grib_tmp_700: gdal.Dataset, grib_tmp_850: gdal.Dataset, grib_dew_850: gdal.Dataset):
        self.grib_tmp_700: gdal.Dataset = grib_tmp_700
        self.grib_tmp_850: gdal.Dataset = grib_tmp_850
        self.grib_dew_850: gdal.Dataset = grib_dew_850


class SeverityEnum(Enum):
    """ Enumerated values for severity
    """
    LOW = "<4"
    MODERATE = "4-8"
    HIGH = "8-11"
    EXTREME = ">11"


severity_levels = [item.value for item in SeverityEnum]


def get_severity_string(severity: int) -> str:
    """ Return the severity level as a string, e.g. severity level 3 maps to "11+"
    """
    return severity_levels[severity]
