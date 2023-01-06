"""
Methods for processing snow coverage data
"""

import io
import logging
import os
import tempfile
import numpy as np
from osgeo import gdal, osr
from app import config
from app.utils.s3 import get_client


BASE_URL = 'https://n5eil02u.ecs.nsidc.org/egi/request?' \
    'short_name=VNP10A1F&version=1&bounding_box=-139.06,48.3,-114.03,60&page_size=100'
RAW_SNOW_COVERAGE_NAME = 'raw_snow_coverage.tif'
SNOW_COVERAGE_NAME = 'snow_coverage.tif'
SNOW_COVERAGE_MASK_NAME = 'snow_coverage_mask.tif'
SNOW_COVERAGE_MASK_3857_NAME = 'snow_coverage_mask_3857.tif'
SNOW_COVERAGE_COG_NAME = 'snow_coverage_cog.tif'

logger = logging.getLogger(__name__)


class FileLikeObject(io.IOBase):
    """ Very basic wrapper of the SpooledTemporaryFile to expose the file-like object interface.

    The aiobotocore library expects a file-like object, but we can't pass the SpooledTemporaryFile
    object directly to aiobotocore. aiobotocore looks for a "tell" method, which isn't present
    on SpooledTemporaryFile. aiobotocore doesn't need an object with a tell method, and understands
    how to use IOBase, so we can wrap the SpooledTemporaryFile in a class that implements IOBase
    to make aiobotocore happy.
    """

    def __init__(self, file: tempfile.SpooledTemporaryFile):
        super().__init__()
        self.file = file

    def read(self, size: int = -1):
        return self.file.read(size)

    def write(self, b: bytes):  # pylint: disable=invalid-name
        return self.file.write(b)

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        return self.file.seek(offset, whence)


async def snow_coverage(hfi_path: str, snow_date: str):
    bucket = config.get('OBJECT_STORE_BUCKET')
    s3_path = f'/vsis3/{bucket}/snow_coverage/{snow_date}/'
    key = f'snow_coverage/{snow_date}'
    with tempfile.TemporaryDirectory() as temp_dir:
        process_snow_coverage(hfi_path, s3_path, temp_dir)
        await write_object_to_s3(f'{key}/{SNOW_COVERAGE_NAME}', os.path.join(temp_dir, SNOW_COVERAGE_NAME))
        create_snow_coverage_mask(temp_dir)
        await write_object_to_s3(f'{key}/{SNOW_COVERAGE_MASK_NAME}', os.path.join(temp_dir, SNOW_COVERAGE_MASK_NAME))
        create_snow_mask_cog(temp_dir)
        await write_object_to_s3(f'{key}/{SNOW_COVERAGE_COG_NAME}', os.path.join(temp_dir, SNOW_COVERAGE_COG_NAME))
    return f'{s3_path}{SNOW_COVERAGE_MASK_NAME}'


def process_snow_coverage(hfi_path: str, s3_path: str, temp_dir: str):
    """
    Given a path to a HFI raster from SFMS and the location of a tif containing a mosaic of snow coverage
    data, reproject the snow data tif to Lamber Conformal Conic, clip to the extent of the HFI raster
    and resample to the same resolution as the HFI raster.
    """

    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')

    # Open the raw HFI tiff to use as a source of parameters for the processing of the snow data
    source = gdal.Open(hfi_path, gdal.GA_ReadOnly)
    geo_transform = source.GetGeoTransform()
    x_res = geo_transform[1]
    y_res = -geo_transform[5]
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * source.RasterXSize
    miny = maxy + geo_transform[5] * source.RasterYSize
    extent = [minx, miny, maxx, maxy]
    source_projection = source.GetProjection()

    # The filename of the snow mosaic in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    raw_snow_coverage_path = f'{s3_path}{RAW_SNOW_COVERAGE_NAME}'
    snow_coverage_output_path = os.path.join(temp_dir, SNOW_COVERAGE_NAME)
    # Perform reprojection to Lambert Conformal Conic, crop extent and resample to 2km x 2km pixels
    gdal.Warp(snow_coverage_output_path, raw_snow_coverage_path, dstSRS=source_projection,
              outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)


def create_snow_coverage_mask(temp_dir: str):
    """
    Given a path to snow coverage data, re-classify the data to act as a mask for future HFI processing.
    A NDSI (ie. snow coverage) value between 0-100 represent snow coverage. Here we define snow coverage
    between 10-100. We need to consult the literature or data scientists on proper use of NDSI.
    """
    snow_coverage_path = os.path.join(temp_dir, SNOW_COVERAGE_NAME)
    source = gdal.Open(snow_coverage_path, gdal.GA_ReadOnly)
    source_band = source.GetRasterBand(1)
    source_data = source_band.ReadAsArray()
    # In the classified data 0 is assigned to snow covered pixels which will 'cancel' HFI values
    # when the rasters are multiplied later on. QA values in the original data are assigned a value
    # of 1 so they dont impact HFI calculations for now.
    classified = np.where((source_data > 10) & (source_data <= 100), 0, 1)
    output_driver = gdal.GetDriverByName("GTiff")
    snow_mask_path = os.path.join(temp_dir, SNOW_COVERAGE_MASK_NAME)
    snow_mask = output_driver.Create(snow_mask_path, xsize=source_band.XSize,
                                     ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
    snow_mask.SetGeoTransform(source.GetGeoTransform())
    snow_mask.SetProjection(source.GetProjection())
    snow_mask_band = snow_mask.GetRasterBand(1)
    # snow_mask_band.SetNoDataValue(0)
    snow_mask_band.WriteArray(classified)
    snow_mask = None


def create_snow_mask_cog(temp_dir: str):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    destination_srs = srs.ExportToWkt()
    source_path = os.path.join(temp_dir, SNOW_COVERAGE_MASK_NAME)
    source = gdal.Open(source_path, gdal.GA_ReadOnly)
    geo_transform = source.GetGeoTransform()
    x_res = geo_transform[1]
    y_res = -geo_transform[5]
    projected_path = os.path.join(temp_dir, SNOW_COVERAGE_MASK_3857_NAME)
    gdal.Warp(projected_path, source, dstSRS=destination_srs, xRes=x_res, yRes=y_res,
              resampleAlg=gdal.GRA_NearestNeighbour, dstNodata=1, srcNodata=1)
    projected_source = gdal.Open(projected_path, gdal.GA_ReadOnly)
    projected_source.BuildOverviews('NEAREST', [2, 4, 8, 16, 32])

    # create teh cloud optimized geotiff
    driver = gdal.GetDriverByName('GTiff')
    output_path = os.path.join(temp_dir, SNOW_COVERAGE_COG_NAME)
    options = ["COPY_SRC_OVERVIEWS=YES", "TILED=YES", "COMPRESS=LZW"]
    # pylint: disable=unused-variable
    cog = driver.CreateCopy(output_path, projected_source, options=options)
    source = None
    projected_source = None
    cog = None


async def write_object_to_s3(key, path):
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        logger.info('Uploading file "%s" to "%s"', path, key)
        with open(path, 'rb') as file:
            await client.put_object(Bucket=bucket,
                                    Key=key,
                                    Body=FileLikeObject(file))
        logger.info('Done uploading file: "%s"', path)
