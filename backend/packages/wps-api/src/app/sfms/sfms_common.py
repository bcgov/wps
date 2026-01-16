"""
Common utilities for SFMS interpolation modules.
"""

import logging
from datetime import datetime
from typing import List
import numpy as np
from osgeo import gdal
from aiohttp import ClientSession
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.wildfire_one.wildfire_fetchers import fetch_raw_dailies_for_all_stations
from wps_shared.wildfire_one.util import is_station_valid
from wps_shared.schemas.stations import WeatherStation
from wps_shared.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


async def fetch_station_actuals(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
    require_elevation: bool = False,
) -> List[SFMSDailyActual]:
    logger.info("Fetching station %s for", time_of_interest)

    station_lookup = {station.code: station for station in stations}
    raw_dailies = await fetch_raw_dailies_for_all_stations(session, headers, time_of_interest)

    records = []
    for raw_daily in raw_dailies:
        try:
            station_data = raw_daily.get("stationData")
            if not is_station_valid(station_data):
                continue

            station_code = station_data.get("stationCode")
            record_type = raw_daily.get("recordType", {}).get("id")

            if record_type != "ACTUAL":
                continue

            if station_code not in station_lookup:
                logger.debug("Station %s not found in station lookup", station_code)
                continue

            station = station_lookup[station_code]

            if require_elevation and station.elevation is None:
                logger.warning("No elevation data for station %s, skipping", station_code)
                continue

            actual = SFMSDailyActual(
                code=station_code,
                lat=station.lat,
                lon=station.long,
                elevation=station.elevation,
                temperature=raw_daily.get("temperature"),
                relative_humidity=raw_daily.get("relativeHumidity"),
                precipitation=raw_daily.get("precipitation"),
                wind_speed=raw_daily.get("windSpeed"),
            )
            records.append(actual)

        except Exception as e:
            logger.error("Error processing daily for station: %s", e, exc_info=True)
            continue

    logger.info("Found %d stations with valid data", len(records))
    return records


def log_interpolation_stats(
    total_pixels: int,
    interpolated_count: int,
    failed_interpolation_count: int,
    skipped_nodata_count: int,
) -> None:
    """
    Log interpolation statistics.

    :param total_pixels: Total number of pixels in the raster
    :param interpolated_count: Number of successfully interpolated pixels
    :param failed_interpolation_count: Number of pixels that failed interpolation
    :param skipped_nodata_count: Number of pixels skipped due to NoData
    """
    logger.info("Interpolation complete:")
    logger.info("  Total pixels: %d", total_pixels)
    logger.info(
        "  Successfully interpolated: %d (%.1f%%)",
        interpolated_count,
        100.0 * interpolated_count / total_pixels if total_pixels > 0 else 0,
    )
    logger.info(
        "  Failed interpolation (no stations in range): %d (%.1f%%)",
        failed_interpolation_count,
        100.0 * failed_interpolation_count / total_pixels if total_pixels > 0 else 0,
    )
    logger.info(
        "  Skipped (NoData): %d (%.1f%%)",
        skipped_nodata_count,
        100.0 * skipped_nodata_count / total_pixels if total_pixels > 0 else 0,
    )

    if interpolated_count == 0:
        logger.warning(
            "WARNING: No pixels were successfully interpolated! Check station locations and coordinate system."
        )


def save_raster_to_geotiff(
    array: np.ndarray,
    geo_transform: tuple,
    projection: str,
    output_path: str,
    nodata_value: float = -9999.0,
) -> None:
    """
    Save a numpy array as a GeoTIFF file.

    :param array: 2D numpy array of values
    :param geo_transform: GDAL geotransform tuple
    :param projection: WKT projection string
    :param output_path: Path to write output GeoTIFF
    :param nodata_value: NoData value for the raster
    """
    output_ds = WPSDataset.from_array(
        array=array,
        geotransform=geo_transform,
        projection=projection,
        nodata_value=nodata_value,
        datatype=gdal.GDT_Float32,
    )

    with output_ds:
        output_ds.export_to_geotiff(output_path)
