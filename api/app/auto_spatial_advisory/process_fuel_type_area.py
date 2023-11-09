""" Code relating to processing high HFI area per fire zone
"""

import logging
from datetime import date, datetime
from time import perf_counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auto_spatial_advisory.run_type import RunType
from app.db.database import get_async_write_session_scope
from app.db.models.auto_spatial_advisory import AdvisoryFuelStats, HighHfiArea
from app.db.crud.auto_spatial_advisory import (get_all_hfi_thresholds, 
                                               get_all_sfms_fuel_types, 
                                               get_high_hfi_fuel_types, 
                                               get_run_parameters_id, 
                                               save_advisory_fuel_stats, 
                                               save_high_hfi_area)


logger = logging.getLogger(__name__)


async def write_high_hfi_area(session: AsyncSession, row: any, run_parameters_id: int):
    high_hfi_area = HighHfiArea(advisory_shape_id=row.shape_id,
                                run_parameters=run_parameters_id,
                                area=row.area,
                                threshold=row.threshold)
    await save_high_hfi_area(session, high_hfi_area)


async def process_fuel_type_area(run_type: RunType, run_datetime: datetime, for_date: date):
    """ Create new fuel type analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info('Processing fuel type area %s for run date: %s, for date: %s', run_type, run_datetime, for_date)
    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

        stmt = select(AdvisoryFuelStats)\
            .where(AdvisoryFuelStats.run_parameters == run_parameters_id)
        
        exists = (await session.execute(stmt)).scalars().first() is not None

        if (not exists):
            # get thresholds data
            thresholds = await get_all_hfi_thresholds(session)
            # get fuel type ids data
            fuel_types = await get_all_sfms_fuel_types(session)
            logger.info('Getting high hfi fuel types...')
            fuel_type_high_hfi_areas = await get_high_hfi_fuel_types(session, run_type, run_datetime, for_date)
            advisory_fuel_stats = []

            for record in fuel_type_high_hfi_areas:
                shape_id = record[0]
                fuel_type_id = record[1]
                threshold_id = record[2]
                # area is stored in square metres in DB. For user convenience, convert to hectares
                # 1 ha = 10,000 sq.m.
                area = record[3] / 10000
                fuel_type_obj = next((ft for ft in fuel_types if ft.fuel_type_id == fuel_type_id), None)
                threshold_obj = next((th for th in thresholds if th.id == threshold_id), None)

                advisory_fuel_stats.append(
                    AdvisoryFuelStats(advisory_shape_id=shape_id, 
                                      threshold=threshold_obj.id, 
                                      run_parameters=run_parameters_id,
                                      fuel_type=fuel_type_obj.id,
                                      area=area)
                    )

            logger.info('Writing advisory fuel stats...')
            await save_advisory_fuel_stats(session, advisory_fuel_stats)
        else:
            logger.info("Advisory fuel stats already processed")

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing high HFI area', delta)
