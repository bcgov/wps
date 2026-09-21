import argparse
import asyncio
import logging
import os
import sys
import tempfile

import aiofiles
from osgeo import gdal

from wps_shared import config
from wps_shared.db.crud.fuel_layer import get_processed_fuel_raster_details
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.geospatial.geospatial import GDALResamplingMethod, warp_to_match_raster
from wps_shared.geospatial.zonal_stats import iter_raster_windows
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)

GEOTIFF_CREATION_OPTIONS = [
    "TILED=YES",
    "BLOCKXSIZE=256",
    "BLOCKYSIZE=256",
    "COMPRESS=DEFLATE",
    "BIGTIFF=IF_SAFER",
]


class MissingFuelTypeRasterError(Exception):
    """Exception thrown when a ready fuel type raster record can't be found."""


def prepare_masked_tif(temp_dir: str, fuel_type_raster_path: str) -> str:
    """Create a classified TPI raster masked to combustible pixels for one fuel grid.

    Fuel codes are nearest-neighbour warped to the TPI grid so categories remain discrete. Both
    rasters are then processed in bounded windows to avoid province-sized in-memory arrays. The
    result supplies fuel-covered area by TPI class during fuel-grid installation.
    """
    set_s3_gdal_config()
    raster_addresser = BaseRasterAddresser()
    tpi_raster_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    fuel_raster_key = raster_addresser.gdal_path(S3Key(fuel_type_raster_path))
    tpi_raster_key = raster_addresser.gdal_path(S3Key(f"dem/tpi/{tpi_raster_name}"))
    fuel_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)  # LCC projection
    tpi_ds: gdal.Dataset = gdal.Open(tpi_raster_key, gdal.GA_ReadOnly)  # BC Albers 3005 projection

    # preserve categorical fuel codes while matching the TPI extent, projection, and pixel size
    warped_fuel_path = os.path.join(temp_dir, "warped_fuel.tif")
    warped_fuel_ds: gdal.Dataset = warp_to_match_raster(
        fuel_ds, tpi_ds, warped_fuel_path, GDALResamplingMethod.NEAREST_NEIGHBOUR
    )

    masked_tpi_dataset: gdal.Dataset | None = None
    try:
        geo_transform = tpi_ds.GetGeoTransform()
        tpi_ds_srs = tpi_ds.GetProjection()
        tpi_band: gdal.Band = tpi_ds.GetRasterBand(1)

        # write a local GeoTIFF because the caller uploads the finished object to S3.
        output_driver: gdal.Driver = gdal.GetDriverByName("GTiff")
        output_path = os.path.join(temp_dir, "fuel_masked_tpi.tif")
        masked_tpi_dataset = output_driver.Create(
            output_path,
            xsize=tpi_band.XSize,
            ysize=tpi_band.YSize,
            bands=1,
            eType=gdal.GDT_Byte,
            options=GEOTIFF_CREATION_OPTIONS,
        )
        masked_tpi_dataset.SetGeoTransform(geo_transform)
        masked_tpi_dataset.SetProjection(tpi_ds_srs)
        masked_fuel_type_band: gdal.Band = masked_tpi_dataset.GetRasterBand(1)
        masked_fuel_type_band.SetNoDataValue(0)
        for window in iter_raster_windows([warped_fuel_ds, tpi_ds]):
            warped_fuel_codes, tpi_classes = window.arrays
            combustible = (warped_fuel_codes > 0) & (warped_fuel_codes < 99)
            # use zero as background so only fuel-covered TPI classes contribute to later statistics
            tpi_classes[~combustible] = 0
            masked_fuel_type_band.WriteArray(tpi_classes, window.x_offset, window.y_offset)
        masked_fuel_type_band.FlushCache()
        return output_path
    finally:
        warped_fuel_ds = None
        fuel_ds = None
        tpi_ds = None
        masked_tpi_dataset = None


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
