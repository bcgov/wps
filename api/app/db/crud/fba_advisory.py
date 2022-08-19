from datetime import date
from app.db.models.advisory import FireZoneAdvisory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def save_advisory(session: AsyncSession, advisory: FireZoneAdvisory):
    session.add(advisory)


async def get_advisories(session: AsyncSession, today: date):
    stmt = select(FireZoneAdvisory).where(FireZoneAdvisory.for_date == today)
    result = await session.execute(stmt)
    return result.scalars()
