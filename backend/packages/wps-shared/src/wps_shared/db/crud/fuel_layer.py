"""CRUD operations relating to processing fuel rasters"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared import config
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


async def save_processed_fuel_raster(session: AsyncSession, processed_raster: FuelTypeRaster):
    """Add a new FuelTypeRaster record."""
    session.add(processed_raster)


async def get_latest_processed_fuel_raster_details(session: AsyncSession, year: int):
    """Retrieve the most recently processed fuel raster based on creation timestamp."""
    stmt = (
        select(FuelTypeRaster)
        .where(FuelTypeRaster.year == year)
        .order_by(FuelTypeRaster.version.desc())
    )
    result = (await session.execute(stmt)).first()
    return result


async def get_processed_fuel_raster_details(
    session: AsyncSession, year: int, version: Optional[int]
) -> Optional[FuelTypeRaster]:
    """
    Retrieve details of a processed fuel raster for a given year and optional version.

    If `version` is None, returns the most recently processed fuel raster for the specified year,
    ordered by descending version number. If `version` is provided, returns the fuel raster
    matching both the specified year and version.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session to use for the query.
        year (int): The year of the fuel raster to retrieve.
        version (Optional[int]): The version of the fuel raster to retrieve. If None, retrieves the latest version.

    Returns:
        Optional[FuelTypeRaster]: The matching FuelTypeRaster object if found, otherwise None.

    Raises:
        AssertionError: If more than one raster is found for the specified year and version.
    """
    if version is None:
        stmt = (
            select(FuelTypeRaster)
            .where(FuelTypeRaster.year == year)
            .order_by(FuelTypeRaster.version.desc())
        )
        result = list((await session.execute(stmt)).scalars().all())
        return None if len(result) == 0 else result[0]
    else:
        stmt = (
            select(FuelTypeRaster)
            .where(FuelTypeRaster.year == year)
            .where(FuelTypeRaster.version == version)
        )
        result = (await session.execute(stmt)).scalars().one_or_none()
        return result


async def get_latest_fuel_type_raster_by_fuel_raster_name(session: AsyncSession, name: str):
    stmt = (
        select(FuelTypeRaster)
        .where(FuelTypeRaster.object_store_path.contains(name))
        .order_by(FuelTypeRaster.version.desc())
    )
    result = await session.execute(stmt)
    return result.scalar()


async def get_fuel_type_raster_by_year(
    session: AsyncSession, year: int
) -> Optional[FuelTypeRaster]:
    """Get the latest fuel type raster for a given year, falling back to the previous year
    if the current year's fuel grid hasn't been updated yet.

    :param session: An async database session.
    :param year: The year to look up.
    :return: A FuelTypeRaster record, or None if not found.
    """
    fuel_raster_name = config.get("FUEL_RASTER_NAME")
    now = get_utc_now()
    if year >= now.year and str(year) not in fuel_raster_name:
        # Covers the case where we have been using last year's fuel grid in the early part of the
        # current fire season (ie. the fuel grid hasn't been updated yet).
        logger.info("No fuel raster for %d in FUEL_RASTER_NAME, falling back to %d", year, year - 1)
        return await get_processed_fuel_raster_details(session, year - 1, None)
    return await get_processed_fuel_raster_details(session, year, None)
