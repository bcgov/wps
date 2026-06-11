"""CRUD operations relating to processing fuel rasters"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.fuel_type_raster import FuelRasterInstallStatus, FuelTypeRaster

logger = logging.getLogger(__name__)


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
            .where(FuelTypeRaster.install_status == FuelRasterInstallStatus.READY)
            .order_by(FuelTypeRaster.version.desc())
        )
        result = list((await session.execute(stmt)).scalars().all())
        return None if len(result) == 0 else result[0]
    else:
        stmt = (
            select(FuelTypeRaster)
            .where(FuelTypeRaster.year == year)
            .where(FuelTypeRaster.version == version)
            .where(FuelTypeRaster.install_status == FuelRasterInstallStatus.READY)
        )
        result = (await session.execute(stmt)).scalars().one_or_none()
        return result


async def get_fuel_type_raster_by_year(
    session: AsyncSession, year: int
) -> Optional[FuelTypeRaster]:
    """Get the latest installed fuel type raster for a requested year.

    If the requested year's grid has not been installed yet, use the most recent prior grid.

    :param session: An async database session.
    :param year: The year to look up.
    :return: A FuelTypeRaster record, or None if not found.
    """
    stmt = (
        select(FuelTypeRaster)
        .where(FuelTypeRaster.year <= year)
        .where(FuelTypeRaster.install_status == FuelRasterInstallStatus.READY)
        .order_by(FuelTypeRaster.year.desc(), FuelTypeRaster.version.desc())
    )
    result = await session.execute(stmt)
    fuel_type_raster = result.scalars().first()
    logger.info(
        "Queried for fuel type raster for year %s, found: %s",
        year,
        fuel_type_raster.object_store_path if fuel_type_raster else None,
    )
    return fuel_type_raster


async def get_ready_fuel_type_raster_by_year_and_hash(
    session: AsyncSession, year: int, content_hash: str
) -> Optional[FuelTypeRaster]:
    """
    Get a ready fuel type raster for the exact year and content hash.

    :param session: An async database session.
    :param year: The fuel grid year to look up.
    :param content_hash: The fuel grid content hash to match.
    :return: The latest matching FuelTypeRaster record, or None if not found.
    """
    stmt = (
        select(FuelTypeRaster)
        .where(
            FuelTypeRaster.year == year,
            FuelTypeRaster.content_hash == content_hash,
            FuelTypeRaster.install_status == FuelRasterInstallStatus.READY,
        )
        .order_by(FuelTypeRaster.version.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
