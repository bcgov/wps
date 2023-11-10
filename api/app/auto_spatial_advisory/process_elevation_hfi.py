""" Code relating to processing HFI data related to elevation
"""
import logging
from datetime import date, datetime
from time import perf_counter
from app.auto_spatial_advisory.common import get_s3_key
from app.auto_spatial_advisory.elevation import process_elevation
from app.auto_spatial_advisory.run_type import RunType

logger = logging.getLogger(__name__)


async def process_hfi_elevation(run_type: RunType, run_date: date, run_datetime: datetime, for_date: date):
    """ Create a new elevation based hfi analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    logger.info('Processing HFI elevation %s for run date: %s, for date: %s', run_type, run_date, for_date)
    perf_start = perf_counter()

    key = get_s3_key(run_type, run_date, for_date)
    logger.info(f'Key to HFI in object storage: {key}')

    await process_elevation(key, run_type, run_datetime, for_date)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing HFI elevatioon', delta)
