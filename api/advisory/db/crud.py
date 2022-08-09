""" Create/Read/Update/Delete """
from datetime import date
from typing import List
from sqlalchemy import select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from advisory.db.models.tileserver import (Hfi, FireZone)


async def get_hfi_area_percentages(session: AsyncSession, for_date: date) -> List[Row]:
    """ This is terribly slow!

    For each fire zone, it gives you the area of the fire zone, and the area of hfi polygons
    within that fire zone. Using those two values, you can then calculate the percentage of the
    zone that has a high hfi.
    """
    stmt = select(FireZone.id,
                  FireZone.mof_fire_zone_id,
                  FireZone.mof_fire_zone_name,
                  FireZone.geom.ST_Transform(3005).ST_Area().label('zone_area'),
                  Hfi.wkb_geometry.ST_Union().ST_Intersection(FireZone.geom).ST_Transform(3005).ST_Area().label('hfi_area'))\
        .join(Hfi, Hfi.wkb_geometry.ST_Intersects(FireZone.geom))\
        .where(Hfi.date == for_date)\
        .group_by(FireZone.id)
    result = await session.execute(stmt)
    return result.all()

    # return session.query(
    #     FireZone.id,
    #     FireZone.mof_fire_zone_id,
    #     FireZone.mof_fire_zone_name,
    #     FireZone.geom.ST_Transform(3005).ST_Area().label('zone_area'),
    #     Hfi.wkb_geometry.ST_Union().ST_Intersection(FireZone.geom).ST_Transform(3005).ST_Area().label('hfi_area'))\
    #     .join(Hfi, Hfi.wkb_geometry.ST_Intersects(FireZone.geom))\
    #     .filter(Hfi.date == for_date)\
    #     .group_by(FireZone.id)
