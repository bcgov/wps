from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.psu import FireCentre


async def get_fire_centres(session: AsyncSession):
    statement = select(FireCentre)
    result = await session.execute(statement)
    return result.scalars()
