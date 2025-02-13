import logging
import os
import numpy as np
from osgeo import gdal
from wps_shared import config
from wps_shared.db.models.snow import ProcessedSnow

SNOW_COVERAGE_WARPED_NAME = 'snow_coverage_warped.tif'
SNOW_COVERAGE_MASK_NAME = 'snow_coverage_mask.tif'
MASKED_HFI_PATH_NAME = 'masked_hfi.tif'

logger = logging.getLogger(__name__)


def classify_snow_mask(snow_path: str, temp_dir: str):
    """
    Given a path to snow coverage data, re-classify the data to act as a mask for future HFI processing.
    A NDSI (ie. snow coverage) value between 0-100 represent snow coverage. Here we define snow coverage
    between 10-100. We need to consult the literature or data scientists on proper use of NDSI.
    """
    source = gdal.Open(snow_path, gdal.GA_ReadOnly)
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
    snow_mask_band.WriteArray(classified)
    snow_mask_band = None
    snow_mask = None
    source_data = None
    source_band = None
    source = None
    return os.path.join(temp_dir, SNOW_COVERAGE_MASK_NAME)


async def prepare_snow_mask(hfi_path: str, last_processed_snow: ProcessedSnow, temp_dir: str):

    # Open the HFI tiff to use as a source of parameters for preparation of the snow mask
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

    bucket = config.get('OBJECT_STORE_BUCKET')
    for_date = last_processed_snow.for_date
    # The filename of the snow coverage tiff in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    snow_key = f"/vsis3/{bucket}/snow_coverage/{for_date.strftime('%Y-%m-%d')}/clipped_snow_coverage_{for_date.strftime('%Y-%m-%d')}_epsg4326.tif"
    snow_mask_warped_output_path = os.path.join(temp_dir, SNOW_COVERAGE_WARPED_NAME)
    # Perform reprojection to Lambert Conformal Conic to match HFI data, crop extent and resample to 2km x 2km pixels
    gdal.Warp(snow_mask_warped_output_path, snow_key, dstSRS=source_projection,
              outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)
    source = None
    return snow_mask_warped_output_path
    
def apply_snow_mask_to_hfi(hfi_path: str, snow_mask_path: str, temp_dir: str):
    # Open the hfi data
    source_tiff = gdal.Open(hfi_path, gdal.GA_ReadOnly)
    source_band = source_tiff.GetRasterBand(1)
    source_data = source_band.ReadAsArray()

    # Open the snow mask
    snow_tiff = gdal.Open(snow_mask_path, gdal.GA_ReadOnly)
    snow_band = snow_tiff.GetRasterBand(1)
    snow_data = snow_band.ReadAsArray()

    # The snow mask tiff has values of 0 or 1 where 0 represents areas covered by snow and 1 represents
    # snow free areas. Multiply the rasters to apply the mask.
    masked_data = np.multiply(source_data, snow_data)
    masked_hfi_path = os.path.join(temp_dir, MASKED_HFI_PATH_NAME)
    output_driver = gdal.GetDriverByName("GTiff")
    # Create an object with the same dimensions as the hfi input
    masked_hfi_tiff = output_driver.Create(masked_hfi_path, xsize=source_band.XSize,
                                       ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
    # Set the geotransform and projection to the same as the input.
    masked_hfi_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
    masked_hfi_tiff.SetProjection(source_tiff.GetProjection())

    # Write the classified data to the band.
    masked_hfi_tiff_band = masked_hfi_tiff.GetRasterBand(1)
    masked_hfi_tiff_band.SetNoDataValue(0)
    masked_hfi_tiff_band.WriteArray(masked_data)

    # Explicit delete to make sure underlying resources are cleared up!
    source_data = None
    source_band = None
    source_tiff = None
    snow_data = None
    snow_band = None
    snow_tiff = None
    masked_hfi_tiff_band = None
    masked_hfi_tiff = None

    return masked_hfi_path


async def apply_snow_mask(hfi_path: str, last_processed_snow: ProcessedSnow, temp_dir: str):
    gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', config.get('OBJECT_STORE_SECRET'))
    gdal.SetConfigOption('AWS_ACCESS_KEY_ID', config.get('OBJECT_STORE_USER_ID'))
    gdal.SetConfigOption('AWS_S3_ENDPOINT', config.get('OBJECT_STORE_SERVER'))
    gdal.SetConfigOption('AWS_VIRTUAL_HOSTING', 'FALSE')

    snow_mask_path = await prepare_snow_mask(hfi_path, last_processed_snow, temp_dir)
    snow_masked_classified_path = classify_snow_mask(snow_mask_path, temp_dir)
    hfi_snow_masked_path = apply_snow_mask_to_hfi(hfi_path, snow_masked_classified_path, temp_dir)
    return hfi_snow_masked_path
