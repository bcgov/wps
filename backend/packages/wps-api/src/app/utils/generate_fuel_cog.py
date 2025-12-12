import logging
import os
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal

from wps_shared import config
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.cog import reproject_raster, generate_cloud_optimized_geotiff
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)

bucket = config.get("OBJECT_STORE_BUCKET")

# Input
INPUT_GEOTIFF = f"/vsis3/{bucket}/psu/rasters/fuel/FM_FUEL_TYPE_GRID_BC_2025_500m_BC_ONLY.tif"
# Output
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "fbp2025_500m_cog.tif")


def reclassify_fuel_array(array: np.ndarray, no_data_value=None) -> np.ndarray:
    reclassified = np.copy(array)
    reclassified[np.isin(array, [2010, 2060, 2070])] = 8
    reclassified[array == 2030] = 10
    reclassified[np.isin(array, [2050, 2080])] = 12
    reclassified[(array >= 500) & (array <= 595)] = 14
    reclassified[array == 2020] = 14
    reclassified[np.isin(array, [2000, 2040])] = 99

    # set the no data value to 255, the max for byte data type
    if no_data_value is not None:
        reclassified[array == no_data_value] = 255
    return reclassified


def reclassify_fuel_geotiff(fuel_raster_path: str, output_geotiff_path: str) -> str:
    """
    Reclassify the fuel grid raster -- typically needed for high res prometheus fuel grid.
    The reclassification rules are based on the lookup table for the 2025 fuel grid in s3:
    {bucket}/psu/rasters/fuel
    """
    ds: gdal.Dataset = gdal.Open(fuel_raster_path)
    band: gdal.Band = ds.GetRasterBand(1)
    array = band.ReadAsArray()

    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    no_data_value = band.GetNoDataValue()

    reclassified = reclassify_fuel_array(array, no_data_value)

    ds = None

    with WPSDataset.from_array(reclassified, transform, projection, 255, gdal.GDT_Byte) as ds:
        ds.export_to_geotiff(output_geotiff_path)

    logger.info(f"Reclassification complete. Output saved to: {output_geotiff_path}")
    return output_geotiff_path


if __name__ == "__main__":
    set_s3_gdal_config()
    configure_logging()

    with TemporaryDirectory() as temp_dir:
        # Define paths for intermediate and final outputs
        reclass_geotiff = os.path.join(temp_dir, "fuel_grid_reclassified.tif")
        reprojected_path = os.path.join(temp_dir, "fuel_grid_reprojected.tif")

        # Reclassify the fuel grid raster
        logger.info(f"Processing {INPUT_GEOTIFF} ...")
        reclassified_path = reclassify_fuel_geotiff(INPUT_GEOTIFF, reclass_geotiff)

        # Reproject to EPSG:3857
        reprojected_path = reproject_raster(
            reclassified_path, reprojected_path, target_srs="EPSG:3857"
        )

        # Generate COG
        generate_cloud_optimized_geotiff(reprojected_path, OUTPUT_PATH)
