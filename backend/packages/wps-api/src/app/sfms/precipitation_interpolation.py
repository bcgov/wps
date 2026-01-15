"""
Precipitation interpolation using Inverse Distance Weighting (IDW).

This module implements the SFMS precipitation interpolation workflow:
1. Fetch station data from WF1
2. Interpolate precipitation to raster using IDW
"""

import logging
from datetime import datetime
from typing import List
import numpy as np
from aiohttp import ClientSession
from wps_shared.schemas.stations import WeatherStation
from wps_shared.schemas.sfms import StationPrecipitation
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from app.sfms.sfms_common import (
    fetch_station_observations,
    log_interpolation_stats,
    save_raster_to_geotiff,
)

logger = logging.getLogger(__name__)


async def fetch_station_precipitation(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
) -> List[StationPrecipitation]:
    """
    Fetch precipitation data from WF1 for all stations with values.

    :param session: aiohttp ClientSession for making requests
    :param headers: Authentication headers for WF1 API
    :param time_of_interest: The datetime to fetch observations for
    :param stations: List of WeatherStation objects
    :return: List of StationPrecipitation objects with valid precipitation readings
    """

    def create_precipitation_record(
        station_code: int, station: WeatherStation, value: float
    ) -> StationPrecipitation:
        return StationPrecipitation(
            code=station_code,
            lat=station.lat,
            lon=station.long,
            precipitation=value,
        )

    return await fetch_station_observations(
        session=session,
        headers=headers,
        time_of_interest=time_of_interest,
        stations=stations,
        field_name="precipitation",
        create_record=create_precipitation_record,
        require_elevation=False,
    )


def interpolate_precipitation_to_raster(
    stations: List[StationPrecipitation],
    reference_raster_path: str,
    output_path: str,
) -> str:
    """
    Interpolate station precipitation to a raster using IDW.

    :param stations: List of StationPrecipitation objects
    :param reference_raster_path: Path to reference raster (defines grid)
    :param output_path: Path to write output precipitation raster
    :return: Path to output raster
    """
    logger.info("Starting precipitation interpolation for %d stations", len(stations))

    if stations:
        logger.info("Station locations:")
        for station in stations[:5]:
            logger.info(
                "  Station %d: lat=%.4f, lon=%.4f, precip=%.1fmm",
                station.code,
                station.lat,
                station.lon,
                station.precipitation,
            )

    station_lats = [s.lat for s in stations if s.precipitation is not None]
    station_lons = [s.lon for s in stations if s.precipitation is not None]
    station_values = [s.precipitation for s in stations if s.precipitation is not None]

    logger.info("Using %d stations with valid precipitation", len(station_lats))

    with WPSDataset(reference_raster_path) as ref_ds:
        geo_transform = ref_ds.ds.GetGeoTransform()
        if geo_transform is None:
            raise ValueError(
                f"Failed to get geotransform from reference raster: {reference_raster_path}"
            )
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        lats, lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords()

        total_pixels = x_size * y_size
        skipped_nodata_count = total_pixels - len(valid_yi)

        logger.info("Interpolating precipitation for raster grid (%d x %d)", x_size, y_size)
        logger.info(
            "Processing %d valid pixels (skipping %d NoData pixels)",
            len(valid_yi),
            skipped_nodata_count,
        )

        logger.info(
            "Running batch IDW interpolation for %d pixels and %d stations",
            len(lats),
            len(station_lats),
        )
        station_lats_array = np.array(station_lats)
        station_lons_array = np.array(station_lons)
        station_values_array = np.array(station_values)

        interpolated_values = idw_interpolation(
            lats, lons, station_lats_array, station_lons_array, station_values_array
        )
        assert isinstance(interpolated_values, np.ndarray)

        precip_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

        interpolation_succeeded = ~np.isnan(interpolated_values)
        interpolated_count = int(np.sum(interpolation_succeeded))
        failed_interpolation_count = len(interpolated_values) - interpolated_count

        for idx in np.where(interpolation_succeeded)[0]:
            precip_array[valid_yi[idx], valid_xi[idx]] = interpolated_values[idx]

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        save_raster_to_geotiff(precip_array, geo_transform, projection, output_path)

        logger.info("Precipitation interpolation complete: %s", output_path)
        return output_path
