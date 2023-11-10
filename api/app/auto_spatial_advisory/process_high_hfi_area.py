""" Code relating to processing high HFI area per fire zone
"""


import logging
from datetime import date, datetime
from sqlalchemy.future import select
from time import perf_counter
from sqlalchemy.ext.asyncio import AsyncSession
from app.auto_spatial_advisory.run_type import RunType
from app.db.database import get_async_write_session_scope
from app.db.models.auto_spatial_advisory import HighHfiArea
from app.db.crud.auto_spatial_advisory import get_run_parameters_id, calculate_high_hfi_areas, save_high_hfi_area


logger = logging.getLogger(__name__)


async def write_high_hfi_area(session: AsyncSession, row: any, run_parameters_id: int):
    high_hfi_area = HighHfiArea(advisory_shape_id=row.shape_id,
                                run_parameters=run_parameters_id,
                                area=row.area,
                                threshold=row.threshold)
    await save_high_hfi_area(session, high_hfi_area)


async def process_high_hfi_area(run_type: RunType, run_datetime: datetime, for_date: date):
    """ Create new high hfi area analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info('Processing high HFI area %s for run date: %s, for date: %s', run_type, run_datetime, for_date)
    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

        stmt = select(HighHfiArea)\
            .where(HighHfiArea.run_parameters == run_parameters_id)
        
        exists = (await session.execute(stmt)).scalars().first() is not None

        if (not exists):
            logger.info('Getting high HFI area per zone...')
            high_hfi_areas = await calculate_high_hfi_areas(session, run_type, run_datetime, for_date)

            logger.info('Writing high HFI areas...')
            for row in high_hfi_areas:
                await write_high_hfi_area(session, row, run_parameters_id)
        else:
            logger.info("High hfi area already processed")

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing high HFI area', delta)
