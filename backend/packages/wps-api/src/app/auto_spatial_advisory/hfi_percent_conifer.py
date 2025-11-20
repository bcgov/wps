import argparse
import asyncio
import logging
from datetime import date, datetime
from time import perf_counter
from typing import Optional

import numpy as np
from geoalchemy2.shape import to_shape
from osgeo import gdal, osr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_spatial_advisory.common import get_hfi_s3_key
from app.auto_spatial_advisory.fuel_type_layer import (
    get_fuel_type_raster_by_year,
)
from wps_shared.db.crud.auto_spatial_advisory import (
    get_fire_zone_unit_shape_type_id,
    get_fire_zone_units,
    get_run_parameters_by_id,
    get_run_parameters_id,
    get_sfms_mixed_fuel_type,
    get_table_srid,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import AdvisoryHFIPercentConifer, Shape
from wps_shared.geospatial.geospatial import prepare_wkt_geom_for_gdal, rasters_match
from wps_shared.run_type import RunType
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

osr.UseExceptions()
gdal.UseExceptions()

logger = logging.getLogger(__name__)


async def get_percent_conifer_s3_key(for_date: date, s3_client: S3Client) -> Optional[str]:
    """
    Gets the S3 key for the percent conifer file for the given year
    or the previous year, if available.
    """
    # check to see if the previous years conifer file exists, only going back 1 year
    current_year = for_date.year
    last_year = current_year - 1

    for year in [current_year, last_year]:
        key = f"sfms/static/m12_{year}.tif"
        if await s3_client.all_objects_exist(key):
            logger.info(f"Found percent conifer grid - {key}")
            return f"/vsis3/{s3_client.bucket}/{key}"
    logger.error(f"No percent conifer key found for {current_year} or {last_year}")
    return None


async def process_hfi_percent_conifer(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Entry point for calculating minimum percent conifer for hfi > 4000 (above advisory level)

    :param run_type: The run type, either forecast or actual.
    :param run_datetime: The date and time of the sfms run in UTC.
    :param for_date: The date being calculated for.
    """
    logger.info(
        f"Calculating minimum percent conifer for {run_type} run type on run date: {run_datetime}, for date: {for_date}"
    )
    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(
            session, RunType(run_type), run_datetime, for_date
        )
        stmt = select(AdvisoryHFIPercentConifer).where(
            AdvisoryHFIPercentConifer.run_parameters == run_parameters_id
        )
        exists = (await session.execute(stmt)).scalars().first() is not None

        if exists:
            logger.info("HFI percent conifer already processed.")
            return

        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        await process_min_percent_conifer_by_zone(
            session,
            run_parameters_id,
            RunType(run_type),
            run_datetime,
            for_date,
            fuel_type_raster.id,
        )

    delta = perf_counter() - perf_start
    logger.info(f"delta count before and after calculating minimum hfi percent conifer: {delta}")


async def process_min_percent_conifer_by_zone(
    session: AsyncSession,
    run_parameters_id: int,
    run_type: RunType,
    run_datetime: date,
    for_date: date,
    fuel_type_raster_id: int,
):
    set_s3_gdal_config()
    # fetch all fire zones from DB
    mixed_fuel_record = await get_sfms_mixed_fuel_type(session)
    fire_zone_shape_type_id = await get_fire_zone_unit_shape_type_id(session)
    zone_units = await get_fire_zone_units(session, fire_zone_shape_type_id)
    srid = await get_table_srid(session, Shape) or 3005  # default to bc albers

    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(srid)

    async with S3Client() as s3_client:
        pct_conifer_key = await get_percent_conifer_s3_key(for_date, s3_client)
    if not pct_conifer_key:
        return

    hfi_key = get_hfi_s3_key(run_type, run_datetime, for_date)

    all_hfi_conifer_percent_to_save: list[AdvisoryHFIPercentConifer] = []
    with gdal.Open(pct_conifer_key) as conifer_ds, gdal.Open(hfi_key) as hfi_ds:
        if not rasters_match(conifer_ds, hfi_ds):
            logger.error(f"{pct_conifer_key} and {hfi_key} do not match.")
            return
        for zone in zone_units:
            zone_wkb = zone.geom
            shapely_geom = to_shape(zone_wkb)
            zone_wkt = shapely_geom.wkt
            zone_geom = prepare_wkt_geom_for_gdal(zone_wkt, source_srs)

            warp_options = gdal.WarpOptions(
                cutlineWKT=zone_geom, cutlineSRS=zone_geom.GetSpatialReference(), cropToCutline=True
            )

            conifer_path = "/vsimem/percent_conifer.tif"
            intersected_ds: gdal.Dataset = gdal.Warp(conifer_path, conifer_ds, options=warp_options)
            pct_conifer_clip = intersected_ds.GetRasterBand(1).ReadAsArray()

            hfi_path = "/vsimem/zone_hfi.tif"
            intersected_ds: gdal.Dataset = gdal.Warp(hfi_path, hfi_ds, options=warp_options)
            hfi_array_clip = intersected_ds.GetRasterBand(1).ReadAsArray()

            # make sure the previous in-memory files are deleted before the next loop
            gdal.Unlink(conifer_path)
            gdal.Unlink(hfi_path)

            min_pct_conifer = get_minimum_percent_conifer_for_hfi(pct_conifer_clip, hfi_array_clip)

            if min_pct_conifer:
                record = AdvisoryHFIPercentConifer(
                    advisory_shape_id=zone.id,
                    fuel_type=mixed_fuel_record.id,
                    run_parameters=run_parameters_id,
                    min_percent_conifer=int(min_pct_conifer),
                    fuel_type_raster_id=fuel_type_raster_id,
                )
                all_hfi_conifer_percent_to_save.append(record)

    await save_all_percent_conifer(session, all_hfi_conifer_percent_to_save)


def get_minimum_percent_conifer_for_hfi(
    pct_conifer_array: np.ndarray, hfi_array: np.ndarray
) -> float:
    """
    Extracts the minimum percent conifer given an array of hfi data and a threshold.
    The percent conifer grid only has values above 0 where there is M-1/M-2 fuel type in the fuel grid.

    :param pct_conifer_array: Array of wind speed values extracted from raster
    :param hfi_array: Array of hfi values extracted from raster
    :return: minimum percent conifer
    """
    mask = (hfi_array > 4000) & (pct_conifer_array > 0)
    min_pct_conifer = np.nanmin(pct_conifer_array[mask]) if np.any(mask) else None

    return min_pct_conifer


async def save_all_percent_conifer(
    session: AsyncSession, hfi_min_percent_conifer: list[AdvisoryHFIPercentConifer]
):
    logger.info("Writing HFI Advisory Minimum Percent Conifer")
    session.add_all(hfi_min_percent_conifer)


## Helper functions for local testing


async def start_hfi_percent_conifer(args: argparse.Namespace):
    async with get_async_write_session_scope() as db_session:
        run_parameters = await get_run_parameters_by_id(db_session, int(args.run_parameters_id))
        if not run_parameters:
            return

        run_param = run_parameters[0]
        run_type, run_datetime, for_date = (
            run_param.run_type,
            run_param.run_datetime,
            run_param.for_date,
        )
        await process_hfi_percent_conifer(run_type, run_datetime, for_date)


def main():
    parser = argparse.ArgumentParser(description="Process hfi percent conifer from command line")
    parser.add_argument(
        "-r",
        "--run_parameters_id",
        help="The id of the run parameters of interest from the run_parameters table",
    )

    args = parser.parse_args()

    asyncio.run(start_hfi_percent_conifer(args))


if __name__ == "__main__":
    configure_logging()
    main()
