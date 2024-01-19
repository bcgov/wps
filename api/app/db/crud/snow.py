""" CRUD operations relating to processing snow coverage
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.snow import ProcessedSnow, SnowSourceEnum


async def save_processed_snow(session: AsyncSession, processed_snow: ProcessedSnow):
    """ Add a new ProcessedSnow record.

    :param processed_snow: The record to be saved.List of actual weather values
    :type processed_snow: ProcessedSnow
    """
    session.add(processed_snow)


async def get_last_processed_snow_by_source(session: AsyncSession, snow_source: SnowSourceEnum) -> ProcessedSnow:
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