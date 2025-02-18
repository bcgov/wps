""" CRUD operations relating to processing snow coverage
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.snow import ProcessedSnow, SnowSourceEnum


async def save_processed_snow(session: AsyncSession, processed_snow: ProcessedSnow):
    """ Add a new ProcessedSnow record.

    :param processed_snow: The record to be saved.List of actual weather values
    :type processed_snow: ProcessedSnow
    """
    session.add(processed_snow)


async def get_last_processed_snow_by_source(session: AsyncSession, snow_source: SnowSourceEnum = SnowSourceEnum.viirs) -> ProcessedSnow:
    """ Retrieve the record with the most recent for_date of the specified snow source.

    :param snow_source: The source of snow data of interest.
    :type snow_source: SnowSourceEnum
    :return: A record containing the last date for which snow data from the specified source was successfully processed.
    :rtype: ProcessedSnow
    """
    stmt = select(ProcessedSnow)\
        .where(ProcessedSnow.snow_source == snow_source)\
        .order_by(ProcessedSnow.for_date.desc())
    result = await session.execute(stmt)
    return result.first()

async def get_most_recent_processed_snow_by_date(session: AsyncSession, target_date: datetime, snow_source: SnowSourceEnum = SnowSourceEnum.viirs) -> ProcessedSnow:
    """ Retreive the most recent record prior or equal to the provided date.

    :param target_date: The date of interest
    :type target_date: datetime
    :param snow_source: The source of snow data of interest.
    :type snow_source: SnowSourceEnum
    :return: A record containing the last date for which snow data from the specified source was successfully processed.
    :rtype: ProcessedSnow
    """
    stmt = select(ProcessedSnow)\
    .where(ProcessedSnow.snow_source == snow_source)\
    .where(ProcessedSnow.for_date <= target_date)\
    .order_by(ProcessedSnow.for_date.desc())
    result = await session.execute(stmt)
    return result.first()