from datetime import date
import logging
from time import perf_counter
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row
from app.db.models.advisory import FireZoneAdvisory, Shape, ShapeType, ClassifiedHfi


logger = logging.getLogger(__name__)


async def save_advisory(session: AsyncSession, advisory: FireZoneAdvisory):
    session.add(advisory)


async def get_advisories(session: AsyncSession, today: date):
    stmt = select(FireZoneAdvisory).where(FireZoneAdvisory.for_date == today)
    result = await session.execute(stmt)
    return result.scalars()


async def save_hfi(session: AsyncSession, hfi: ClassifiedHfi):
    session.add(hfi)


async def get_hfi(session: AsyncSession, for_date: date):
    stmt = select(ClassifiedHfi).where(ClassifiedHfi.date == for_date)
    result = await session.execute(stmt)
    return result.scalars()


async def get_hfi_area_percentages(session: AsyncSession, for_date: date) -> List[Row]:
    """ This is terribly slow!

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the
    zone that has a high hfi.
    """
    perf_start = perf_counter()
    stmt = select(Shape.id,
                  Shape.source_identifier,
                  Shape.geom.ST_Area().label('zone_area'),
                  ClassifiedHfi.geom.ST_Union().ST_Intersection(Shape.geom).ST_Area().label('hfi_area'))\
        .join(ClassifiedHfi, ClassifiedHfi.geom.ST_Intersects(Shape.geom))\
        .where(ClassifiedHfi.date == for_date)\
        .group_by(Shape.id)
    result = await session.execute(stmt)
    all_hfi_percentages = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after hfi area / complex fire zone query', delta)
    return all_hfi_percentages
