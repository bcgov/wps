""" Code relating to processing HFI GeoTIFF files as COGS files.
"""
import logging
import os
from datetime import date
from time import perf_counter
import tempfile
from osgeo import gdal
from app import config
from app.auto_spatial_advisory.common import RunType, get_date_part, get_tiff_key
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.utils.s3 import get_client
from app.utils.time import get_vancouver_now
from app.auto_spatial_advisory.common import get_prefix


logger = logging.getLogger(__name__)


def get_cogs_target_filename(hfi_tiff_key: str) -> str:
    """ Get the target filename, something that looks like this:
    bucket/sfms/upload/forecast/[issue date NOT TIME]/hfi20220823.tif
    bucket/sfms/upload/actual/[issue date NOT TIME]/hfi20220823.tif
    """
    # We are assuming that the local server time, matches the issue date. We assume that
    # right after a file is generated, this API is called - and as such the current
    # time IS the issue date.
    issue_date = get_vancouver_now()
    # depending on the issue date, we decide if it's a forecast or actual.
    prefix = get_prefix(os.path.basename(hfi_tiff_key))

    hfi_date = get_date_part(os.path.basename(hfi_tiff_key))

    cogs_file = f'cogs{hfi_date}.tif'

    # create the filename
    return os.path.join('cogs', 'uploads', prefix, issue_date.isoformat()[:10], cogs_file)


async def process_cogs(run_type: RunType, run_date: date, for_date: date):
    """ Create and store a new cogs tiff for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info('Processing HFI %s for run date: %s, for date: %s', run_type, run_date, for_date)

    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')

    perf_start = perf_counter()
    hfi_tiff_key = get_tiff_key(run_type, run_date, for_date)
    with tempfile.TemporaryDirectory() as temp_dir:

        classified_hfi_temp_filename = os.path.join(temp_dir, 'classified.tif')
        classify_hfi(hfi_tiff_key, classified_hfi_temp_filename)
        # Read the source data.
        cogs_temp_filename = os.path.join(temp_dir, 'cogs.tif')
        source_tiff = gdal.Open(classified_hfi_temp_filename, gdal.GA_ReadOnly)
        cogs_tiff = gdal.Translate(cogs_temp_filename, source_tiff, format="COG")
        # Important to make sure data is flushed to disk!
        cogs_tiff.FlushCache()

        # Explicit delete to make sure underlying resources are cleared up!
        del source_tiff
        del cogs_tiff
        # Get an async S3 client.
        async with get_client() as (client, bucket):
            # We save the Last-modified and Create-time as metadata in the object store - just
            # in case we need to know about it in the future.
            cogs_key = get_cogs_target_filename(hfi_tiff_key)
            with open(cogs_temp_filename, mode='rb') as file:  # b is important -> binary
                fileContent = file.read()
                logger.info('Uploading file "%s" to "%s"', cogs_temp_filename, cogs_key)
                await client.put_object(Bucket=bucket,
                                        Key=cogs_key,
                                        Body=fileContent)
                logger.info('Done uploading file')

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing COGS file', delta)
