"""CRUD operations relating to processing snow coverage"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster


async def save_processed_fuel_raster(session: AsyncSession, processed_raster: FuelTypeRaster):
    """Add a new FuelTypeRaster record."""
    session.add(processed_raster)


async def get_most_recent_fuel_layer(session: AsyncSession) -> FuelTypeRaster:
    """Retrieve the most recently processed fuel raster based on creation timestamp."""
    stmt = select(FuelTypeRaster).order_by(FuelTypeRaster.create_timestamp.desc())
    result = await session.execute(stmt)
    return result.first()
