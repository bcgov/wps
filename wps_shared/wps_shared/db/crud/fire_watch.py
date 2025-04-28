from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.fire_watch import BurnStatusEnum, FireWatch
from wps_shared.db.models.hfi_calc import FireCentre

async def get_all_active_fire_watches(session: AsyncSession):
    statement = select(FireWatch).where(FireWatch.status == BurnStatusEnum.ACTIVE)
    result = await session.execute(statement)
    return result.scalars()

async def get_fire_centre_by_name(session: AsyncSession, name: str) -> FireCentre:
    statement = select(FireCentre).where(FireCentre.name.ilike(name))
    result = await session.execute(statement)
    return result.scalar_one()

async def get_fire_watch_by_id(session: AsyncSession, id: int) -> FireWatch:
    statement = select(FireWatch).where(FireWatch.id == id)
    result = await session.execute(statement)
    return result.scalar_one()

async def save_fire_watch(session: AsyncSession, fire_watch: FireWatch):
    """
    Save a new FireWatch and return the id of the new record.

    :param session: Async db session.
    :param fire_watch: The FireWatch record to save.
    :return: The id of the new FireWatch record.
    """
    session.add(fire_watch)
    await session.commit()
    return fire_watch.id