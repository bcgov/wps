""" CRUD operations relating to processing snow coverage
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.snow import ProcessedSnow, SnowSourceEnum


async def save_processed_snow(session: AsyncSession, processed_snow: ProcessedSnow):
    """ Add a new ProcessedSnow record.
    """
    session.add(processed_snow)


async def get_last_processed_snow_by_source(session: AsyncSession, snow_source: SnowSourceEnum):
    """ Retrieve the record with the most recent for_date of the specified snow source.
    """
    stmt = select(ProcessedSnow)\
        .where(ProcessedSnow.snow_source == snow_source)\
        .order_by(ProcessedSnow.for_date.desc())
    result = await session.execute(stmt)
    return result.first()