""" CRUD operations relating to processing grass curing
"""
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from wps_shared.db.models.grass_curing import PercentGrassCuring

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


def get_percent_grass_curing_by_station_for_date_range(session: Session, start_date: date, end_date: date, station_codes: list[int]):
    """ Given a list of stations, a start date and an end date, return the percent grass curing from processed CWFIS data
        for each station and each date in the specidifed range.

    :param session: A session object for asynchronous database access.
    :type session: AsyncSession
    :param start_date: The first date to return data for.
    :type start_date: datetime.date
    :param ned_date: The last date to return data for.
    :type start_date: datetime.date
    :param station_codes: A list of station codes.
    :type station_codes: List[int]
    """

    stmt = select(PercentGrassCuring)\
        .filter(PercentGrassCuring.for_date.between(start_date, end_date))\
        .filter(PercentGrassCuring.station_code.in_(station_codes))\
        .order_by(PercentGrassCuring.station_code)
    return session.execute(stmt)
        
