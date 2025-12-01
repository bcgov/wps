"""Code relating to processing HFI data related to elevation"""

import logging
from datetime import date, datetime
from time import perf_counter
from app.auto_spatial_advisory.elevation import process_elevation_tpi
from wps_shared.run_type import RunType

logger = logging.getLogger(__name__)


async def process_hfi_elevation(run_type: RunType, run_datetime: datetime, for_date: date):
    """Create a new elevation based hfi analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the sfms run in UTC. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    logger.info("Processing HFI elevation %s for run date: %s, for date: %s", run_type, run_datetime, for_date)
    perf_start = perf_counter()

    await process_elevation_tpi(run_type, run_datetime, for_date)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after processing HFI elevation", delta)
