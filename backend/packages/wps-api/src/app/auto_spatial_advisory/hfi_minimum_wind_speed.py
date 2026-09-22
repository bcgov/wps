import argparse
import asyncio
import logging
from datetime import date, datetime
from time import perf_counter

import numpy as np
from sqlalchemy import select
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
    get_hfi_threshold_ids,
    get_run_parameters_by_id,
    get_run_parameters_id,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryHFIWindSpeed,
    HfiClassificationThresholdEnum,
)
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import iter_raster_windows
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context
from wps_shared.utils.time import convert_to_sfms_timezone
from wps_shared.wps_logging import configure_logging

from app.auto_spatial_advisory.common import get_hfi_s3_key

logger = logging.getLogger(__name__)

ADVISORY_NAME = HfiClassificationThresholdEnum.ADVISORY.value
WARNING_NAME = HfiClassificationThresholdEnum.WARNING.value


def get_wind_spd_s3_key(run_type: RunType, run_datetime: datetime, for_date: date):
    bucket = config.get("OBJECT_STORE_BUCKET")
    sfms_run_datetime = convert_to_sfms_timezone(run_datetime)
    return (
        f"/vsis3/{bucket}/sfms/uploads/{run_type.value}/"
        f"{sfms_run_datetime.date().isoformat()}/wind_speed{for_date:%Y%m%d}.tif"
    )


def update_minimum_wind_by_zone(
    minimum_wind_speed_by_zone_and_threshold: dict[tuple[int, str], float],
    zones: np.ndarray,
    raw_hfi: np.ndarray,
    wind_speed: np.ndarray,
    zone_nodata: float | int,
    wind_nodata: float | None,
) -> None:
    """Merge one window into minimum wind speeds keyed by zone and HFI threshold.

    The accumulator is shared across raster windows and is updated in place. Keys use raster
    source identifiers and threshold names; zones without qualifying pixels are omitted.
    """
    valid_zone_pixels = zones != zone_nodata
    valid_wind_pixels = np.isfinite(wind_speed)
    if wind_nodata is not None:
        # update the existing mask in place to avoid allocating another result array
        # equivalent to: valid_wind_pixels = valid_wind_pixels & (wind_speed != wind_nodata)
        valid_wind_pixels &= wind_speed != wind_nodata
    hfi_threshold_masks = {
        ADVISORY_NAME: (raw_hfi >= 4000) & (raw_hfi < 10000),
        WARNING_NAME: raw_hfi >= 10000,
    }
    for threshold_name, hfi_mask in hfi_threshold_masks.items():
        included_pixels = valid_zone_pixels & valid_wind_pixels & hfi_mask
        selected_zone_ids = zones[included_pixels]
        selected_wind_speeds = wind_speed[included_pixels]
        for source_identifier in np.unique(selected_zone_ids):
            zone_wind_speeds = selected_wind_speeds[selected_zone_ids == source_identifier]
            value = float(np.min(zone_wind_speeds))
            key = (int(source_identifier), threshold_name)
            minimum_wind_speed_by_zone_and_threshold[key] = min(
                minimum_wind_speed_by_zone_and_threshold.get(key, value), value
            )


def calculate_minimum_wind_by_zone(
    zone_path: str, raw_hfi_path: str, wind_path: str
) -> dict[tuple[int, str], float]:
    """Return minimum wind speeds by raster zone source ID and HFI threshold across all windows."""
    minimum_wind_speed_by_zone_and_threshold: dict[tuple[int, str], float] = {}
    with (
        WPSDataset(zone_path) as zones,
        WPSDataset(raw_hfi_path) as raw_hfi,
        WPSDataset(wind_path) as wind,
    ):
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        wind_nodata = wind.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_raster_windows([zones, raw_hfi, wind]):
            zone_ids, raw_hfi_values, wind_values = window.arrays
            update_minimum_wind_by_zone(
                minimum_wind_speed_by_zone_and_threshold,
                zone_ids,
                raw_hfi_values,
                wind_values,
                zone_nodata,
                wind_nodata,
            )
    return minimum_wind_speed_by_zone_and_threshold


async def process_hfi_min_wind_speed(run_type: RunType, run_datetime: datetime, for_date: date):
    """Store minimum wind speed by zone and HFI threshold using rasters."""
    run_type = RunType(run_type)
    logger.info(
        "Processing minimum HFI wind speed for run type: %s, run datetime: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
    )
    perf_start = perf_counter()
    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        exists = await session.scalar(
            select(AdvisoryHFIWindSpeed.id)
            .where(AdvisoryHFIWindSpeed.run_parameters == run_parameters_id)
            .limit(1)
        )
        if exists is not None:
            logger.info("HFI minimum wind speed already processed")
            return

        logger.info("Calculating minimum wind speed by fire zone and HFI threshold")
        with gdal_s3_context():
            minimums = calculate_minimum_wind_by_zone(
                BaseRasterAddresser().get_fire_zone_units_path(),
                get_hfi_s3_key(run_type, run_datetime, for_date),
                get_wind_spd_s3_key(run_type, run_datetime, for_date),
            )
        shape_ids = await get_advisory_shape_ids_by_source_identifier(session)
        thresholds = await get_hfi_threshold_ids(session)
        logger.info("Writing %d HFI minimum wind speed records", len(minimums))
        session.add_all(
            AdvisoryHFIWindSpeed(
                advisory_shape_id=shape_ids[source_identifier],
                threshold=thresholds[threshold_name],
                run_parameters=run_parameters_id,
                min_wind_speed=minimum,
            )
            for (source_identifier, threshold_name), minimum in minimums.items()
        )

    logger.info("Processed minimum HFI wind speed in %.2f seconds", perf_counter() - perf_start)


async def start_hfi_wind_speed(args: argparse.Namespace):
    async with get_async_write_session_scope() as session:
        run_parameters = await get_run_parameters_by_id(session, int(args.run_parameters_id))
        if run_parameters:
            run = run_parameters[0]
            await process_hfi_min_wind_speed(run.run_type, run.run_datetime, run.for_date)


def main():
    parser = argparse.ArgumentParser(description="Process HFI wind speed from the command line")
    parser.add_argument("-r", "--run_parameters_id", required=True)
    asyncio.run(start_hfi_wind_speed(parser.parse_args()))


if __name__ == "__main__":
    configure_logging()
    main()
