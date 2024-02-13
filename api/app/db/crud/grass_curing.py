""" CRUD operations relating to processing grass curing
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.db.models.grass_curing import PercentGrassCuring


async def save_percent_grass_curing(session: AsyncSession, percent_grass_curing: PercentGrassCuring):
    """ Add a new PercentGrassCuring record.

    :param session: A session object for asynchronous database access.
    :type session: AsyncSession
    :param percent_grass_curing: The record to be saved.
    :type percent_grass_curing: PercentGrassCuring
    """
    session.add(percent_grass_curing)


async def get_last_percent_grass_curing_for_date(session: AsyncSession):
    """ Get the last date for which a PercentGrassCuring record exists.
    
    :param session: A session object for asynchronous database access.
    :type session: AsyncSession
    """
    stmt = select(func.max(PercentGrassCuring.for_date))
    result = await session.execute(stmt)
    return result.scalar()
