import argparse
import asyncio
import logging
from datetime import date, datetime
from time import perf_counter

import numpy as np
from geoalchemy2.shape import to_shape
from osgeo import gdal, osr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    get_fire_zone_unit_shape_type_id,
    get_fire_zone_units,
    get_hfi_threshold_ids,
    get_run_parameters_by_id,
    get_run_parameters_id,
    get_table_srid,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    HfiClassificationThresholdEnum,
    AdvisoryHFIWindSpeed,
    Shape,
)
from wps_shared.geospatial.geospatial import prepare_wkt_geom_for_gdal, rasters_match
from wps_shared.wps_logging import configure_logging
from wps_shared.run_type import RunType
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.time import convert_to_sfms_timezone

from app.auto_spatial_advisory.common import get_hfi_s3_key

osr.UseExceptions()
gdal.UseExceptions()

logger = logging.getLogger(__name__)


def get_wind_spd_s3_key(run_type: RunType, run_datetime: datetime, for_date: date):
    bucket = config.get("OBJECT_STORE_BUCKET")
    sfms_run_datetime = convert_to_sfms_timezone(run_datetime)
    key = f"/vsis3/{bucket}/sfms/uploads/{run_type.value}/{sfms_run_datetime.date().isoformat()}/wind_speed{for_date.strftime('%Y%m%d')}.tif"
    return key


async def process_hfi_min_wind_speed(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Entry point for calculating minimum wind speed for each advisory threshold

    :param run_type: The run type, either forecast or actual.
    :param run_datetime: The date and time of the sfms run in UTC.
    :param for_date: The date being calculated for.
    """
    logger.info(
        f"Calculating minimum wind speed for {run_type} run type on run date: {run_datetime}, for date: {for_date}"
    )
    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(
            session, RunType(run_type), run_datetime, for_date
        )
        stmt = select(AdvisoryHFIWindSpeed).where(
            AdvisoryHFIWindSpeed.run_parameters == run_parameters_id
        )
        exists = (await session.execute(stmt)).scalars().first() is not None

        if exists:
            logger.info("HFI minimum wind speed already processed.")
            return

        await process_min_wind_speed_by_zone(
            session, run_parameters_id, RunType(run_type), run_datetime, for_date
        )

    delta = perf_counter() - perf_start
    logger.info(f"delta count before and after calculating minimum hfi wind speed: {delta}")


async def process_min_wind_speed_by_zone(
    session: AsyncSession,
    run_parameters_id: int,
    run_type: RunType,
    run_datetime: date,
    for_date: date,
):
    """
    Calculates minimum wind speed for each advisory threshold per fire zone unit. Determines the minimum wind speed by
    comparing wind speed and hfi rasters. Where the hfi raster meets a certain threshold, the wind speed will be taken
    at the same pixel location. The minimum of each class threshold is then determined and stored.

    :param session: Async database session
    :param run_parameters_id: The RunParameters object id
    :param run_type: The run type, either forecast or actual.
    :param run_datetime: The date and time of the sfms run.
    :param for_date: The date being calculated for.
    """
    set_s3_gdal_config()
    # fetch all fire zones from DB
    fire_zone_shape_type_id = await get_fire_zone_unit_shape_type_id(session)
    zone_units = await get_fire_zone_units(session, fire_zone_shape_type_id)
    srid = await get_table_srid(session, Shape) or 3005  # default to bc albers
    advisory_id_lut = await get_hfi_threshold_ids(session)

    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(srid)

    wind_speed_key = get_wind_spd_s3_key(run_type, run_datetime, for_date)
    hfi_key = get_hfi_s3_key(run_type, run_datetime, for_date)

    all_hfi_min_wind_speeds_to_save: list[AdvisoryHFIWindSpeed] = []
    with gdal.Open(wind_speed_key) as wind_ds, gdal.Open(hfi_key) as hfi_ds:
        if not rasters_match(wind_ds, hfi_ds):
            logger.error(f"{wind_speed_key} and {hfi_key} do not match.")
            return
        for zone in zone_units:
            zone_wkb = zone.geom
            shapely_geom = to_shape(zone_wkb)
            zone_wkt = shapely_geom.wkt
            zone_geom = prepare_wkt_geom_for_gdal(zone_wkt, source_srs)

            warp_options = gdal.WarpOptions(
                cutlineWKT=zone_geom, cutlineSRS=zone_geom.GetSpatialReference(), cropToCutline=True
            )

            wind_path = "/vsimem/zone_wind.tif"
            intersected_ds: gdal.Dataset = gdal.Warp(wind_path, wind_ds, options=warp_options)
            wind_band = intersected_ds.GetRasterBand(1)
            wind_array_clip = wind_band.ReadAsArray()
            wind_nodata = wind_band.GetNoDataValue()

            hfi_path = "/vsimem/zone_hfi.tif"
            intersected_ds: gdal.Dataset = gdal.Warp(hfi_path, hfi_ds, options=warp_options)
            hfi_array_clip = intersected_ds.GetRasterBand(1).ReadAsArray()

            # make sure the previous in-memory files are deleted before the next loop
            gdal.Unlink(wind_path)
            gdal.Unlink(hfi_path)

            # Compute minimum wind speed for each HFI range
            hfi_min_wind_speeds = get_minimum_wind_speed_for_hfi(
                wind_array_clip, hfi_array_clip, advisory_id_lut, wind_nodata
            )

            records_to_save = create_hfi_wind_speed_record(
                zone.id, hfi_min_wind_speeds, run_parameters_id
            )

            all_hfi_min_wind_speeds_to_save.extend(records_to_save)

    await save_all_hfi_wind_speeds(session, all_hfi_min_wind_speeds_to_save)


def get_minimum_wind_speed_for_hfi(
    wind_speed_array: np.ndarray,
    hfi_array: np.ndarray,
    advisory_id_lut: dict[str, int],
    wind_nodata_value: float | None,
) -> dict[int, float | None]:
    """
    Calculates the minimum wind speed for each HfiClassificationThresholdEnum given a wind speed array and an hfi array.

    :param wind_speed_array: Array of wind speed values extracted from raster
    :param hfi_array: Array of hfi values extracted from raster
    :param advisory_id_lut: Lookup table for advisory/warning id's
    :param wind_nodata_value: NoData value from wind speed raster
    :return: Dict of advisory level and it's corresponding minimum wind speed
    """
    hfi_class_ids = {
        advisory_id_lut[HfiClassificationThresholdEnum.ADVISORY.value]: (hfi_array >= 4000)
        & (hfi_array < 10000),
        advisory_id_lut[HfiClassificationThresholdEnum.WARNING.value]: (hfi_array >= 10000),
    }

    if wind_nodata_value is not None:  # convert nodata values to np.nan
        wind_speed_array = np.where(wind_speed_array == wind_nodata_value, np.nan, wind_speed_array)

    # Compute minimum wind speed for each classification
    min_wind_speeds: dict[int, float | None] = {}
    for hfi_class, mask in hfi_class_ids.items():
        min_wind_speeds[hfi_class] = np.nanmin(wind_speed_array[mask]) if np.any(mask) else None

    return min_wind_speeds


def create_hfi_wind_speed_record(
    zone_unit_id: int, hfi_min_wind_speeds: dict[int, float | None], run_parameters_id: int
) -> list[AdvisoryHFIWindSpeed]:
    """
    Creates a list of HFIMinWindSpeed records for a given fire zone.
    """
    return [
        AdvisoryHFIWindSpeed(
            advisory_shape_id=zone_unit_id,
            threshold=hfi_class_id,
            run_parameters=run_parameters_id,
            min_wind_speed=wind_speed,
        )
        for hfi_class_id, wind_speed in hfi_min_wind_speeds.items()
        if wind_speed is not None
    ]


async def save_all_hfi_wind_speeds(
    session: AsyncSession, hfi_wind_speeds: list[AdvisoryHFIWindSpeed]
):
    logger.info("Writing HFI Advisory Minimum Wind Speeds")
    session.add_all(hfi_wind_speeds)


## Helper functions for local testing


async def start_hfi_wind_speed(args: argparse.Namespace):
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
        await process_hfi_min_wind_speed(run_type, run_datetime, for_date)


def main():
    parser = argparse.ArgumentParser(description="Process hfi wind speed from command line")
    parser.add_argument(
        "-r",
        "--run_parameters_id",
        help="The id of the run parameters of interest from the run_parameters table",
    )

    args = parser.parse_args()

    asyncio.run(start_hfi_wind_speed(args))


if __name__ == "__main__":
    configure_logging()
    main()
