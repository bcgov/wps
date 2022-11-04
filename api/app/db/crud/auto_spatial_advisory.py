from datetime import date, datetime
from enum import Enum
import logging
from time import perf_counter
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row
from app.db.models.auto_spatial_advisory import (
    Shape, ClassifiedHfi, HfiClassificationThreshold, RunTypeEnum, FuelType)


logger = logging.getLogger(__name__)


class HfiClassificationThresholdEnum(Enum):
    """ Enum for the different HFI classification thresholds. """
    ADVISORY = 'advisory'
    WARNING = 'warning'


async def get_hfi_classification_threshold(session: AsyncSession, name: HfiClassificationThresholdEnum) -> HfiClassificationThreshold:
    stmt = select(HfiClassificationThreshold).where(
        HfiClassificationThreshold.name == name.value)
    result = await session.execute(stmt)
    return result.scalars().first()


async def save_hfi(session: AsyncSession, hfi: ClassifiedHfi):
    session.add(hfi)


async def save_fuel_type(session: AsyncSession, fuel_type: FuelType):
    session.add(fuel_type)


async def get_hfi(session: AsyncSession, run_type: RunTypeEnum, run_date: datetime, for_date: date):
    stmt = select(ClassifiedHfi).where(
        ClassifiedHfi.run_type == run_type,
        ClassifiedHfi.for_date == for_date,
        ClassifiedHfi.run_datetime == run_date)
    result = await session.execute(stmt)
    return result.scalars()


async def get_combustible_area(session: AsyncSession):
    """ Get the combustible area for each "shape". This is slow, and we don't expect it to run
    in real time.

    This method isn't being used right now, but you can calculate the combustible area for each
    zone as follows:

    ```python
    from app.db.crud.auto_spatial_advisory import get_combustible_area
    from app.db.database import get_async_read_session_scope

    async with get_async_read_session_scope() as session:
    result = await get_combustible_area(session)

    for record in result:
        print(record)
        print(record['combustible_area']/record['zone_area'])
    ```

    """
    logger.info('starting zone/combustible area intersection query')
    perf_start = perf_counter()
    stmt = select(Shape.id,
                  Shape.source_identifier,
                  Shape.geom.ST_Area().label('zone_area'),
                  FuelType.geom.ST_Union().ST_Intersection(Shape.geom).ST_Area().label('combustible_area'))\
        .join(FuelType, FuelType.geom.ST_Intersects(Shape.geom))\
        .where(FuelType.fuel_type_id.not_in((-10000, 99, 100, 102, 103)))\
        .group_by(Shape.id)
    result = await session.execute(stmt)
    all_combustible = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after hfi area + zone/area intersection query', delta)
    return all_combustible


async def get_hfi_area(session: AsyncSession,
                       run_type: RunTypeEnum,
                       run_datetime: datetime,
                       for_date: date) -> List[Row]:
    """ This is slow - but not terribly slow.

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the
    zone that has a high hfi.
    """
    logger.info('starting zone/area intersection query')
    perf_start = perf_counter()
    stmt = select(Shape.id,
                  Shape.source_identifier,
                  Shape.combustible_area,
                  Shape.geom.ST_Area().label('zone_area'),
                  ClassifiedHfi.geom.ST_Union().ST_Intersection(Shape.geom).ST_Area().label('hfi_area'))\
        .join(ClassifiedHfi, ClassifiedHfi.geom.ST_Intersects(Shape.geom))\
        .where(ClassifiedHfi.run_type == run_type,
               ClassifiedHfi.for_date == for_date,
               ClassifiedHfi.run_datetime == run_datetime)\
        .group_by(Shape.id)
    result = await session.execute(stmt)
    all_hfi = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after hfi area + zone/area intersection query', delta)
    return all_hfi
