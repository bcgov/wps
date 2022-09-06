""" Create/Read/Update/Delete """
from datetime import date
import logging
from time import perf_counter
from typing import List
from sqlalchemy import select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from advisory.db.models.tileserver import (Hfi, FireZone)

logger = logging.getLogger(__name__)


async def get_hfi_area_percentages(session: AsyncSession, for_date: date) -> List[Row]:
    """ DEPRECATED?

    This is terribly slow!

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the
    zone that has a high hfi.
    """
    perf_start = perf_counter()
    stmt = select(FireZone.id,
                  FireZone.mof_fire_zone_id,
                  FireZone.mof_fire_zone_name,
                  FireZone.combustible_area,
                  FireZone.geom.ST_Transform(3005).ST_Area().label('zone_area'),
                  Hfi.wkb_geometry.ST_Union().ST_Intersection(FireZone.geom)
                  .ST_Transform(3005).ST_Area().label('hfi_area'))\
        .join(Hfi, Hfi.wkb_geometry.ST_Intersects(FireZone.geom))\
        .where(Hfi.date == for_date)\
        .group_by(FireZone.id)
    result = await session.execute(stmt)
    all_hfi_percentages = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after hfi area / complex fire zone query', delta)
    return all_hfi_percentages
