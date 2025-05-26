"""CRUD operations relating to processing fuel rasters"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster


async def save_processed_fuel_raster(session: AsyncSession, processed_raster: FuelTypeRaster):
    """Add a new FuelTypeRaster record."""
    session.add(processed_raster)


async def get_most_recent_fuel_layer(
    session: AsyncSession, year: int, version: int
) -> Optional[FuelTypeRaster]:
    """Retrieve the most recently processed fuel raster based on creation timestamp."""
    stmt = (
        select(FuelTypeRaster)
        .where(FuelTypeRaster.year == year)
        .where(FuelTypeRaster.version == version)
    )
    result = list((await session.execute(stmt)).all())
    assert len(result) < 2
    return None if len(result) == 0 else result[0]
