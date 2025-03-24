import os
from wps_shared.run_type import RunType
from datetime import date, datetime

from wps_shared.utils.time import convert_to_sfms_timezone


def get_pmtiles_filepath(run_datetime: datetime, run_type: RunType, filename: str) -> str:
    """
    Get the file path for both reading and writing the pmtiles from/to the object store.
    Example: {bucket}/psu/pmtiles/hfi/actual/[issue/run_date]/hfi[for_date].pmtiles


    :param run_datetime: The date and time of the run to process. (when was the hfi file created?)
    :param run_type: forecast or actual
    :param filename: hfi[for_date].pmtiles -> hfi20230821.pmtiles
    :return: s3 bucket key for pmtiles file
    """
    sfms_run_date = convert_to_sfms_timezone(run_datetime).date()
    pmtiles_filepath = os.path.join("psu", "pmtiles", "hfi", run_type.value, sfms_run_date.strftime("%Y-%m-%d"), filename)

    return pmtiles_filepath


def get_pmtiles_filename(for_date: date):
    """
    Returns the object store filename for a pmtiles file based on a given for_date.

    :param for_date: the date the hfi pmtiles is forecasted for
    :return: filename string
    """
    return f'hfi{for_date.strftime("%Y%m%d")}.pmtiles'


def get_snow_masked_hfi_filepath(run_datetime: datetime, run_type: RunType, filename: str) -> str:
    """
    Get the file path for both reading and writing the tif raster from/to the object store.
    Example: {bucket}/psu/rasters/hfi/actual/[issue/run_date]/snow_masked_hfi[for_date].tif


    :param run_datetime: The datetime of the run to process. (when was the hfi file created?)
    :param run_type: forecast or actual
    :param filename: snow_masked_hfi[for_date].tif -> snow_masked_hfi20230821.tif
    :return: s3 bucket key for raster file
    """
    sfms_run_datetime = convert_to_sfms_timezone(run_datetime)
    raster_filepath = os.path.join("psu", "rasters", "hfi", run_type.value, sfms_run_datetime.strftime("%Y-%m-%d"), filename)

    return raster_filepath


def get_raster_tif_filename(for_date: date) -> str:
    """
    Returns the object store filename for a raster tif based on a given for_date.

    :param for_date: the date the hfi tif is forecasted for
    :return: filename string
    """
    return f'snow_masked_hfi{for_date.strftime("%Y%m%d")}.tif'
