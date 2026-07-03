import argparse
import asyncio
import logging
import os
import sys
import tempfile

import aiofiles
import numpy as np
from osgeo import gdal

from wps_shared import config
from wps_shared.db.crud.fuel_layer import get_processed_fuel_raster_details
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.geospatial.geospatial import GDALResamplingMethod, warp_to_match_raster
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)


class MissingFuelTypeRasterError(Exception):
    """Exception thrown when a ready fuel type raster record can't be found."""


def prepare_masked_tif(temp_dir: str, fuel_type_raster_path: str) -> str:
    """
    Creates a static classified TPI raster masked to fuel covered pixels for one fuel grid.

    The result is used to populate tpi_fuel_area, which gives the total fuel covered area in each
    TPI class.
    """
    # Open the rasters with gdal
    set_s3_gdal_config()
    raster_addresser = BaseRasterAddresser()
    tpi_raster_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    fuel_raster_key = raster_addresser.gdal_path(S3Key(fuel_type_raster_path))
    tpi_raster_key = raster_addresser.gdal_path(S3Key(f"dem/tpi/{tpi_raster_name}"))
    fuel_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)  # LCC projection
    tpi_ds: gdal.Dataset = gdal.Open(tpi_raster_key, gdal.GA_ReadOnly)  # BC Albers 3005 projection

    # Warp the fuel raster to match extent, spatial reference and cell size of the TPI raster
    warped_fuel_path = "/vsimem/warped_fuel.tif"
    warped_fuel_ds: gdal.Dataset = warp_to_match_raster(
        fuel_ds, tpi_ds, warped_fuel_path, GDALResamplingMethod.NEAREST_NEIGHBOUR
    )

    # Classify fuel cells as 1 and non-fuel cells as 0 before masking the TPI classes.
    warped_fuel_band: gdal.Band = warped_fuel_ds.GetRasterBand(1)
    warped_fuel_data: np.ndarray = warped_fuel_band.ReadAsArray()
    mask = np.where((warped_fuel_data > 0) & (warped_fuel_data < 99), 1, 0)

    geo_transform = tpi_ds.GetGeoTransform()
    tpi_ds_srs = tpi_ds.GetProjection()
    tpi_band: gdal.Band = tpi_ds.GetRasterBand(1)
    tpi_data = tpi_band.ReadAsArray()

    # write a local GeoTIFF because the caller uploads the finished object to S3.
    masked_tpi_data = np.multiply(mask, tpi_data)
    output_driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    output_path = os.path.join(temp_dir, "fuel_masked_tpi.tif")
    masked_tpi_dataset: gdal.Dataset = output_driver.Create(
        output_path, xsize=tpi_band.XSize, ysize=tpi_band.YSize, bands=1, eType=gdal.GDT_Byte
    )
    masked_tpi_dataset.SetGeoTransform(geo_transform)
    masked_tpi_dataset.SetProjection(tpi_ds_srs)
    masked_fuel_type_band: gdal.Band = masked_tpi_dataset.GetRasterBand(1)
    masked_fuel_type_band.SetNoDataValue(0)
    masked_fuel_type_band.WriteArray(masked_tpi_data)
    fuel_ds = None
    tpi_ds = None
    masked_tpi_dataset = None
    return output_path


def get_fuel_masked_tpi_key(year: int, version: int) -> str:
    classified_tpi_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    classified_tpi_base, _ = os.path.splitext(classified_tpi_name)
    return f"dem/tpi/{classified_tpi_base}_fuel_masked_{year}_v{version}.tif"


async def create_fuel_masked_tpi_raster(year: int, version: int | None = None) -> str:
    """
    Generate and upload the fuel-masked TPI raster for a ready fuel grid.

    :param year: Fuel grid year.
    :param version: Optional fuel grid version. When omitted, the latest ready version is used.
    :return: S3 key for the uploaded fuel-masked TPI raster.
    """
    async with get_async_read_session_scope() as session:
        fuel_type_raster = await get_processed_fuel_raster_details(session, year, version)
    if fuel_type_raster is None:
        raise MissingFuelTypeRasterError("Could not find a ready fuel type raster.")

    masked_tpi_key = get_fuel_masked_tpi_key(fuel_type_raster.year, fuel_type_raster.version)
    async with S3Client() as s3_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            masked_tpi_path = prepare_masked_tif(temp_dir, fuel_type_raster.object_store_path)
            async with aiofiles.open(masked_tpi_path, "rb") as masked_tpi:
                await s3_client.put_object(key=masked_tpi_key, body=await masked_tpi.read())

    logger.info("Generated fuel-masked TPI raster: %s", masked_tpi_key)
    return masked_tpi_key


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the fuel-masked classified TPI raster for a ready fuel grid."
    )
    parser.add_argument("-y", "--year", required=True, type=int, help="Fuel grid year.")
    parser.add_argument(
        "-v",
        "--version",
        type=int,
        default=None,
        help="Fuel grid version. Defaults to the latest ready version for the year.",
    )
    return parser.parse_args()


def main():
    try:
        gdal.UseExceptions()
        args = parse_args()
        asyncio.run(create_fuel_masked_tpi_raster(args.year, args.version))
        sys.exit(os.EX_OK)
    except Exception as exception:
        logger.error("An error occurred while generating fuel-masked TPI.", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
