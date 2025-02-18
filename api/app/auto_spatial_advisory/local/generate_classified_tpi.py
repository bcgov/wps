"""
Classifies relative topographic position raster into valley bottom, mid slope, upper slope classifications.
"""

import asyncio
from osgeo import gdal
import numpy as np
import os
from wps_shared.utils.s3 import get_client
from wps_shared import config


async def generate():
    """
    Retrieves the 50m resolution extended BC raster that has WhiteboxTools' Relative Topographic Position Index applied to it with a window size of 100,.
    It then classifies the indices into these bins, smallest being valley bottom, middle being mid slope, highest being upper slope: (-1, -1/3], (-1/3, 1/3], and (1/3, 1].
    """
    async with get_client() as (client, bucket):
        dem = await client.get_object(Bucket=bucket, Key=f'dem/tpi/{config.get("TPI_DEM_NAME")}')

        mem_path = "/vsimem/dem.tif"
        data = await dem["Body"].read()
        gdal.FileFromMemBuffer(mem_path, data)
        dem_source = gdal.Open(mem_path, gdal.GA_ReadOnly)
        gdal.Unlink(mem_path)

        source_band = dem_source.GetRasterBand(1)
        source_data = source_band.ReadAsArray()

        target_path = os.path.join(os.getcwd(), "bc_dem_50m_tpi_win100_classified.tif")

        # Classify the raster
        # Define the boundaries for binning elevation into bins: (-1, -1/3], (-1/3, 1/3], and (1/3, 1]
        bins = [-1, -1 / 3, 1 / 3, 1]

        # Classify the data into bins
        classified = np.digitize(source_data, bins)

        # Remove any existing target file.
        if os.path.exists(target_path):
            os.remove(target_path)

        output_driver = gdal.GetDriverByName("GTiff")
        # Create an object with the same dimensions as the input, but with 8 bit unsigned values.
        target_tiff = output_driver.Create(target_path, xsize=source_band.XSize, ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
        # Set the geotransform and projection to the same as the input.
        target_tiff.SetGeoTransform(dem_source.GetGeoTransform())
        target_tiff.SetProjection(dem_source.GetProjection())

        # Write the classified data to the band.
        target_band = target_tiff.GetRasterBand(1)

        # The value of 4 was showing up east of BC
        target_band.SetNoDataValue(4)
        target_band.WriteArray(classified)

        # Important to make sure data is flushed to disk!
        target_tiff.FlushCache()

        # Explicit delete to make sure underlying resources are cleared up!
        del source_band
        del dem_source
        del target_band
        del target_tiff
        del output_driver


if __name__ == "__main__":
    asyncio.run(generate())
