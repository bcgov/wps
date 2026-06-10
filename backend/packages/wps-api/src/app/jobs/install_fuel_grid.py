import argparse
import asyncio
import logging
import os
import sys

from osgeo import gdal

from app.fuel_grid.install import FuelGridInstallResult, install_fuel_grid
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)


def log_install_result(result: FuelGridInstallResult) -> None:
    fuel_type_raster = result.fuel_type_raster
    logger.info("Fuel grid install complete")
    logger.info("fuel_type_raster_id: %s", fuel_type_raster.id)
    logger.info("year: %s", fuel_type_raster.year)
    logger.info("version: %s", fuel_type_raster.version)
    logger.info("install_status: %s", fuel_type_raster.install_status)
    logger.info("staged_source_key: %s", result.staged_source_key)
    logger.info("processed_raster_key: %s", fuel_type_raster.object_store_path)
    logger.info("content_hash: %s", fuel_type_raster.content_hash)
    logger.info("fuel_masked_tpi_key: %s", result.fuel_masked_tpi_key)
    counts = result.counts
    logger.info("advisory_fuel_types_count: %s", counts.advisory_fuel_types)
    logger.info("advisory_shape_fuels_count: %s", counts.advisory_shape_fuels)
    logger.info("combustible_area_count: %s", counts.combustible_area)
    logger.info("tpi_fuel_area_count: %s", counts.tpi_fuel_area)
    logger.info("advisory_shape_fuels_duplicate_count: %s", counts.advisory_shape_fuels_duplicates)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install a fuel grid and its derived ASA static data."
    )
    parser.add_argument("-y", "--year", required=True, type=int, help="Fuel grid year to install.")
    parser.add_argument(
        "-k",
        "--key",
        required=True,
        help="Staged object name under sfms/static/, for example fbp2026.tif.",
    )
    return parser.parse_args()


def main():
    try:
        gdal.UseExceptions()
        args = parse_args()
        result = asyncio.run(install_fuel_grid(args.year, args.key))
        if result is not None:
            log_install_result(result)
        sys.exit(os.EX_OK)
    except Exception as exception:
        logger.error("An error occurred while installing fuel grid.", exc_info=exception)
        send_chatops_notification(
            ":scream: Encountered an error while installing fuel grid.", exception
        )
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
