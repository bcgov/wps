import os
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal

from wps_shared import config
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.utils.s3 import set_s3_gdal_config

bucket = config.get("OBJECT_STORE_BUCKET")

# Input
INPUT_GEOTIFF = f"/vsis3/{bucket}/psu/rasters/fuel/FM_FUEL_TYPE_GRID_BC_2025_500m_BC_ONLY.tif"
# Output
OUTPUT_PATH = "/Users/breedwar/Downloads/fbp2025_500m_cog.tif"


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
    ds = gdal.Open(fuel_raster_path)
    band = ds.GetRasterBand(1)
    array = band.ReadAsArray()

    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    no_data_value = band.GetNoDataValue()

    reclassified = reclassify_fuel_array(array, no_data_value)

    ds = None

    with WPSDataset.from_array(reclassified, transform, projection, 255, gdal.GDT_Byte) as ds:
        ds.export_to_geotiff(output_geotiff_path)

    print(f"Reclassification complete. Output saved to: {output_geotiff_path}")
    return output_geotiff_path


def reproject_raster_to_3857(input_path: str, output_path: str) -> str:
    """
    Reproject the raster to EPSG:3857 using GDAL Warp.
    """

    src_ds = gdal.Open(input_path)
    gt = src_ds.GetGeoTransform()
    xres = gt[1]  # pixel width (meters if original CRS uses meters)
    yres = abs(gt[5])  # pixel height

    gdal.Warp(
        output_path,
        input_path,
        dstSRS="EPSG:3857",
        xRes=xres,
        yRes=yres,
        resampleAlg=gdal.GRA_NearestNeighbour,
        format="GTiff",
    )

    print(f"Reprojection complete. Output saved to: {output_path}")
    src_ds = None
    return output_path


def generate_cloud_optimized_geotiff(input_path: str, output_path: str) -> None:
    """
    Generate a Cloud Optimized GeoTIFF (COG) from the input raster.
    """
    src_ds = gdal.Open(input_path)

    cog_options = [
        "COMPRESS=LZW",  # Use LZW compression
        "OVERVIEWS=IGNORE_EXISTING",  # Always create new overviews
        "RESAMPLING=NEAREST",  # Use nearest neighbor resampling for overviews. This will effect how overviews look.
    ]

    cog_driver = gdal.GetDriverByName("COG")

    cog_driver.CreateCopy(output_path, src_ds, options=cog_options)
    print(f"COG created at {output_path}")


if __name__ == "__main__":
    set_s3_gdal_config()

    with TemporaryDirectory() as temp_dir:
        # Define paths for intermediate and final outputs
        reclass_geotiff = os.path.join(temp_dir, "fuel_grid_reclassified.tif")
        reprojected_path = os.path.join(temp_dir, "fuel_grid_reprojected.tif")

        # Reclassify the fuel grid raster
        print(f"Processing {INPUT_GEOTIFF} ...")
        reclassified_path = reclassify_fuel_geotiff(INPUT_GEOTIFF, reclass_geotiff)

        # Reproject the reclassified raster to EPSG:3857
        reprojected_path = reproject_raster_to_3857(reclassified_path, reprojected_path)

        # Generate a Cloud Optimized GeoTIFF (COG) from the reprojected raster
        generate_cloud_optimized_geotiff(reprojected_path, OUTPUT_PATH)
