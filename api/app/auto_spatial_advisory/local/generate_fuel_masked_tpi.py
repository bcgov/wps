import asyncio
import os
import numpy as np
import tempfile
from osgeo import gdal

from app import config
from app.auto_spatial_advisory.process_fuel_type_area import get_fuel_type_s3_key
from app.utils.geospatial import GDALResamplingMethod, warp_to_match_raster
from app.utils.s3 import set_s3_gdal_config
from app.utils.s3_client import S3Client


def prepare_masked_tif(temp_dir: str) -> str:
    """
    Creates a masked TPI raster using a classified TPI raster from S3 storage and masking it using the fuel layer
    also from S3 storage
    """
    # Open up our rasters with gdal
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    tpi_raster_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    fuel_raster_key = get_fuel_type_s3_key(bucket)
    tpi_raster_key = f"/vsis3/{bucket}/dem/tpi/{tpi_raster_name}"
    fuel_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)  # LCC projection
    tpi_ds: gdal.Dataset = gdal.Open(tpi_raster_key, gdal.GA_ReadOnly)  # BC Albers 3005 projection

    # Warp the fuel raster to match extent, spatial reference and cell size of the TPI raster
    warped_fuel_path = "/vsimem/warped_fuel.tif"
    warped_fuel_ds: gdal.Dataset = warp_to_match_raster(fuel_ds, tpi_ds, warped_fuel_path, GDALResamplingMethod.NEAREST_NEIGHBOUR)

    # Convert the warped fuel dataset into a binary mask by classifying fuel cells as 1 and non-fuel cells as 0.
    warped_fuel_band: gdal.Band = warped_fuel_ds.GetRasterBand(1)
    warped_fuel_data: np.ndarray = warped_fuel_band.ReadAsArray()
    mask = np.where((warped_fuel_data > 0) & (warped_fuel_data < 99), 1, 0)

    # Some helpful things for creating the final masked TPI raster
    geo_transform = tpi_ds.GetGeoTransform()
    tpi_ds_srs = tpi_ds.GetProjection()
    tpi_band: gdal.Band = tpi_ds.GetRasterBand(1)
    tpi_data = tpi_band.ReadAsArray()

    # Apply the fuel layer mask to the classified TPI raster and store the result in an in-memory gdal dataset
    masked_tpi_data = np.multiply(mask, tpi_data)
    output_driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    output_path = os.path.join(temp_dir, config.get("CLASSIFIED_TPI_DEM_FUEL_MASKED_NAME"))
    masked_tpi_dataset: gdal.Dataset = output_driver.Create(output_path, xsize=tpi_band.XSize, ysize=tpi_band.YSize, bands=1, eType=gdal.GDT_Byte)
    masked_tpi_dataset.SetGeoTransform(geo_transform)
    masked_tpi_dataset.SetProjection(tpi_ds_srs)
    masked_fuel_type_band: gdal.Band = masked_tpi_dataset.GetRasterBand(1)
    masked_fuel_type_band.SetNoDataValue(0)
    masked_fuel_type_band.WriteArray(masked_tpi_data)
    fuel_ds = None
    tpi_ds = None
    masked_tpi_dataset = None
    return output_path


async def create_fuel_masked_tpi_raster():
    async with S3Client() as s3_client:
        with tempfile.TemporaryDirectory() as temp_dir:
            masked_tpi_path = prepare_masked_tif(temp_dir)
            masked_tpi_key = f"dem/tpi/{config.get("CLASSIFIED_TPI_DEM_FUEL_MASKED_NAME")}"
            await s3_client.put_object(key=masked_tpi_key, body=open(masked_tpi_path, "rb"))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_fuel_masked_tpi_raster())