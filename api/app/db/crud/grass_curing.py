""" CRUD operations relating to processing snow coverage
"""
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.db.models.grass_curing import PercentGrassCuring


def save_all_percent_grass_curing(session: AsyncSession, records: list[PercentGrassCuring]):
    """ Bulk save multiple PercentGrassCuring records.
    
    :param session: A session object for asynchronous database access.
    :type session: AsyncSession
    """
    session.add_all(records)


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


async def get_percent_grass_curing_by_date(session: AsyncSession, for_date: date):
    """ Retrieve the PercentGrassCuring records for all stations for the given date.

    :param session: A session object for asynchronous database access.
    :type session: AsyncSession
    :param for_date: The date of interest.
    :type for_date: Date
    :return: A list of percent grass curing for all stations for the given date.
    :rtype: ProcessedSnow
    """
    stmt = select(PercentGrassCuring)\
        .where(PercentGrassCuring.for_date == for_date)
    result = await session.execute(stmt)
    return result