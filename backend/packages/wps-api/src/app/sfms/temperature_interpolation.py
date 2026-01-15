"""
Temperature interpolation using Inverse Distance Weighting (IDW) with elevation adjustment.

This module implements the SFMS temperature interpolation workflow:
1. Fetch station data from WF1
2. Adjust station temperatures to sea level using dry adiabatic lapse rate
3. Interpolate adjusted temperatures to raster using IDW
4. Adjust raster cell temperatures back to actual elevation using DEM
"""

import logging
import uuid
from datetime import datetime
from typing import List
import numpy as np
from osgeo import gdal
from aiohttp import ClientSession
from wps_shared import config
from wps_shared.schemas.stations import WeatherStation
from wps_shared.schemas.sfms import StationTemperature
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from app.sfms.sfms_common import (
    fetch_station_observations,
    log_interpolation_stats,
    save_raster_to_geotiff,
)

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065


async def fetch_station_temperatures(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
) -> List[StationTemperature]:
    """
    Fetch temperature data from WF1 for all stations with values.

    :param session: aiohttp ClientSession for making requests
    :param headers: Authentication headers for WF1 API
    :param time_of_interest: The datetime to fetch observations for
    :param stations: List of WeatherStation objects with elevation data
    :return: List of StationTemperature objects with valid temperature readings
    """

    def create_temperature_record(
        station_code: int, station: WeatherStation, value: float
    ) -> StationTemperature:
        return StationTemperature(
            code=station_code,
            lat=station.lat,
            lon=station.long,
            elevation=float(station.elevation),  # type: ignore[arg-type]
            temperature=value,
        )

    return await fetch_station_observations(
        session=session,
        headers=headers,
        time_of_interest=time_of_interest,
        stations=stations,
        field_name="temperature",
        create_record=create_temperature_record,
        require_elevation=True,
    )


def adjust_temperature_to_sea_level(station: StationTemperature) -> float:
    """
    Adjust station temperature to sea level (0m elevation) using dry adiabatic lapse rate.

    Temperature decreases by 6.5°C per 1000m of elevation gain.
    To adjust to sea level, we ADD temperature based on elevation:
    T_sea_level = T_station + (elevation * lapse_rate)

    :param station: StationTemperature object with elevation and temperature
    :return: Temperature adjusted to sea level in Celsius
    """
    adjustment = station.elevation * LAPSE_RATE
    sea_level_temp = station.temperature + adjustment
    station.sea_level_temp = sea_level_temp
    return sea_level_temp


def adjust_temperature_to_elevation(sea_level_temp: float, elevation: float) -> float:
    """
    Adjust sea level temperature to actual elevation using dry adiabatic lapse rate.

    Temperature decreases by 6.5°C per 1000m of elevation gain.
    T_elevation = T_sea_level - (elevation * lapse_rate)

    :param sea_level_temp: Temperature at sea level in Celsius
    :param elevation: Elevation in meters
    :return: Temperature adjusted to elevation in Celsius
    """
    adjustment = elevation * LAPSE_RATE
    return sea_level_temp - adjustment


def interpolate_temperature_to_raster(
    stations: List[StationTemperature], reference_raster_path: str, dem_path: str, output_path: str
) -> str:
    """
    Interpolate station temperatures to a raster using IDW and elevation adjustment.

    :param stations: List of StationTemperature objects
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output temperature raster
    :return: Path to output raster
    """
    logger.info("Starting temperature interpolation for %d stations", len(stations))

    if stations:
        logger.info("Station locations:")
        for station in stations[:5]:
            logger.info(
                "  Station %d: lat=%.4f, lon=%.4f, elev=%.1fm, temp=%.1f°C",
                station.code,
                station.lat,
                station.lon,
                station.elevation,
                station.temperature,
            )

    # Adjust all station temperatures to sea level
    for station in stations:
        adjust_temperature_to_sea_level(station)

    station_lats = [s.lat for s in stations if s.sea_level_temp is not None]
    station_lons = [s.lon for s in stations if s.sea_level_temp is not None]
    station_values = [s.sea_level_temp for s in stations if s.sea_level_temp is not None]

    logger.info("Using %d stations with valid sea level temperatures", len(station_lats))

    with WPSDataset(reference_raster_path) as ref_ds:
        geo_transform = ref_ds.ds.GetGeoTransform()
        if geo_transform is None:
            raise ValueError(f"Failed to get geotransform from reference raster: {reference_raster_path}")
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        with WPSDataset(dem_path) as dem_ds:
            logger.info(
                "Resampling DEM from (%d x %d) to match reference (%d x %d)",
                dem_ds.ds.RasterXSize,
                dem_ds.ds.RasterYSize,
                x_size,
                y_size,
            )

            vsimem_path = f"/vsimem/temp_dem_resample_{uuid.uuid4().hex}.tif"
            try:
                resampled_dem = dem_ds.warp_to_match(
                    ref_ds, vsimem_path, resample_method=GDALResamplingMethod.BILINEAR
                )

                dem_band: gdal.Band = resampled_dem.ds.GetRasterBand(1)
                dem_data = dem_band.ReadAsArray()
                if dem_data is None:
                    raise ValueError("Failed to read resampled DEM data")
                dem_nodata = dem_band.GetNoDataValue()

                logger.info("DEM resampled successfully, nodata value: %s", dem_nodata)

                temp_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

                if dem_nodata is not None:
                    valid_mask = dem_data != dem_nodata
                else:
                    valid_mask = np.ones((y_size, x_size), dtype=bool)

                lats, lons, valid_yi, valid_xi = resampled_dem.get_lat_lon_coords(valid_mask)
                valid_elevations = dem_data[valid_mask]

                total_pixels = x_size * y_size
                skipped_nodata_count = total_pixels - len(valid_yi)

                logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)
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

                sea_level_temps = idw_interpolation(
                    lats, lons, station_lats_array, station_lons_array, station_values_array
                )
                assert isinstance(sea_level_temps, np.ndarray)

                interpolation_succeeded = ~np.isnan(sea_level_temps)
                interpolated_count = int(np.sum(interpolation_succeeded))
                failed_interpolation_count = len(sea_level_temps) - interpolated_count

                # Apply elevation adjustment and write to output array
                for idx in np.where(interpolation_succeeded)[0]:
                    actual_temp = adjust_temperature_to_elevation(
                        float(sea_level_temps[idx]), float(valid_elevations[idx])
                    )
                    temp_array[valid_yi[idx], valid_xi[idx]] = actual_temp
            finally:
                try:
                    gdal.Unlink(vsimem_path)
                except RuntimeError:
                    logger.debug("File doesn't exist or already cleaned up")

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        save_raster_to_geotiff(temp_array, geo_transform, projection, output_path)

        logger.info("Temperature interpolation complete: %s", output_path)
        return output_path


def get_dem_path() -> str:
    """
    Get the path to the DEM raster from S3.

    :return: GDAL virtual file system path to DEM
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    return f"/vsis3/{bucket}/sfms/static/bc_elevation.tif"
