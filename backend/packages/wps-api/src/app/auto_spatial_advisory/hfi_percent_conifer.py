import argparse
import asyncio
import logging
from datetime import date, datetime
from time import perf_counter

import numpy as np
from sqlalchemy import select
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
    get_run_parameters_by_id,
    get_run_parameters_id,
    get_sfms_mixed_fuel_type,
)
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import AdvisoryHFIPercentConifer
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import iter_raster_windows
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

from app.auto_spatial_advisory.common import get_hfi_s3_key

logger = logging.getLogger(__name__)


async def get_percent_conifer_s3_key(for_date: date, s3_client: S3Client) -> str | None:
    """Return the current or previous year's percent-conifer raster path."""
    for year in (for_date.year, for_date.year - 1):
        key = f"sfms/static/m12_{year}.tif"
        if await s3_client.all_objects_exist(key):
            logger.info("Found percent conifer grid - %s", key)
            return f"/vsis3/{s3_client.bucket}/{key}"
    logger.error("No percent conifer key found for %s or %s", for_date.year, for_date.year - 1)
    return None


def get_minimum_percent_conifer_for_hfi(
    percent_conifer_array: np.ndarray, hfi_array: np.ndarray
) -> float | None:
    """Return minimum positive percent conifer where HFI is strictly above 4000."""
    mask = (hfi_array > 4000) & (percent_conifer_array > 0) & np.isfinite(percent_conifer_array)
    return float(np.min(percent_conifer_array[mask])) if np.any(mask) else None


def update_minimum_percent_conifer_by_zone(
    minimums: dict[int, float],
    zones: np.ndarray,
    raw_hfi: np.ndarray,
    percent_conifer: np.ndarray,
    zone_nodata: float | int,
) -> None:
    """Merge one window's positive, finite percent-conifer minima where HFI exceeds 4000."""
    valid_zone = zones != zone_nodata
    mask = valid_zone & (raw_hfi > 4000) & (percent_conifer > 0) & np.isfinite(percent_conifer)
    for source_identifier in np.unique(zones[mask]):
        value = float(np.min(percent_conifer[mask & (zones == source_identifier)]))
        source_identifier = int(source_identifier)
        minimums[source_identifier] = min(minimums.get(source_identifier, value), value)


def calculate_minimum_percent_conifer_by_zone(
    zone_path: str, raw_hfi_path: str, percent_conifer_path: str
) -> dict[int, float]:
    """Return percent-conifer minima keyed by zone source ID across all raster windows."""
    minimums: dict[int, float] = {}
    with (
        WPSDataset(zone_path) as zones,
        WPSDataset(raw_hfi_path) as raw_hfi,
        WPSDataset(percent_conifer_path) as percent_conifer,
    ):
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_raster_windows([zones.ds, raw_hfi.ds, percent_conifer.ds]):
            update_minimum_percent_conifer_by_zone(minimums, *window.arrays, zone_nodata)
    return minimums


async def process_hfi_percent_conifer(run_type: RunType, run_datetime: datetime, for_date: date):
    """Store minimum percent conifer by zone using aligned rasters."""
    run_type = RunType(run_type)
    logger.info(
        "Processing minimum HFI percent conifer for run type: %s, run datetime: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
    )
    perf_start = perf_counter()
    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        exists = await session.scalar(
            select(AdvisoryHFIPercentConifer.id)
            .where(AdvisoryHFIPercentConifer.run_parameters == run_parameters_id)
            .limit(1)
        )
        if exists is not None:
            logger.info("HFI percent conifer already processed")
            return

        fuel_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        if fuel_raster is None:
            raise RuntimeError(f"No fuel type raster found for {for_date.year}")
        async with S3Client() as s3_client:
            percent_conifer_path = await get_percent_conifer_s3_key(for_date, s3_client)
        if percent_conifer_path is None:
            return

        logger.info("Calculating minimum percent conifer by fire zone")
        with gdal_s3_context():
            minimums = calculate_minimum_percent_conifer_by_zone(
                BaseRasterAddresser().get_fire_zone_units_path(),
                get_hfi_s3_key(run_type, run_datetime, for_date),
                percent_conifer_path,
            )
        shape_ids = await get_advisory_shape_ids_by_source_identifier(session)
        mixed_fuel = await get_sfms_mixed_fuel_type(session)
        logger.info("Writing %d HFI minimum percent conifer records", len(minimums))
        session.add_all(
            AdvisoryHFIPercentConifer(
                advisory_shape_id=shape_ids[source_identifier],
                fuel_type=mixed_fuel.id,
                run_parameters=run_parameters_id,
                min_percent_conifer=int(minimum),
                fuel_type_raster_id=fuel_raster.id,
            )
            for source_identifier, minimum in minimums.items()
        )

    logger.info(
        "Processed minimum HFI percent conifer in %.2f seconds", perf_counter() - perf_start
    )


async def start_hfi_percent_conifer(args: argparse.Namespace):
    async with get_async_write_session_scope() as session:
        run_parameters = await get_run_parameters_by_id(session, int(args.run_parameters_id))
        if run_parameters:
            run = run_parameters[0]
            await process_hfi_percent_conifer(run.run_type, run.run_datetime, run.for_date)


def main():
    parser = argparse.ArgumentParser(
        description="Process HFI percent conifer from the command line"
    )
    parser.add_argument("-r", "--run_parameters_id", required=True)
    asyncio.run(start_hfi_percent_conifer(parser.parse_args()))


if __name__ == "__main__":
    configure_logging()
    main()
