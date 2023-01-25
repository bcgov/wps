""" Take a classified HFI image and determine distribution of elevations associated with advisory
areas per fire zone.
"""

from datetime import date, datetime
from osgeo import gdal
from time import perf_counter
import logging
import numpy as np
import os
import tempfile
from app import config
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.process_hfi import RunType
from app.db.crud.auto_spatial_advisory import get_run_parameters_id
from app.db.database import get_async_read_session_scope, DB_READ_STRING


logger = logging.getLogger(__name__)


DEM_PATH = '/Users/dareboss/Documents/elevation/dem_mosaic.tif'
TEMP_PATH = '/Users/dareboss/Documents/elevation'
DEM_OUTPUT_PATH = '/Users/dareboss/Documents/elevation/dem'


async def process_elevation(run_type: RunType, run_datetime: datetime, for_date: date):
    """ Create a new elevation statistics record for the given parameters.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    logger.info('Processing elevation stats %s for run date: %s, for date: %s', run_type, run_datetime, for_date)
    perf_start = perf_counter()

    # Get the id from run_parameters associated with the provided runtype, for_date and for_datetime
    async with get_async_read_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type.value, run_datetime, for_date)

    bucket = config.get('OBJECT_STORE_BUCKET')
    # TODO what really has to happen, is that we grab the most recent prediction for the given date,
    # but this method doesn't even belong here, it's just a shortcut for now!
    for_date_string = f'{for_date.year}{for_date.month:02d}{for_date.day:02d}'

    # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    key = f'/vsis3/{bucket}/sfms/uploads/{run_type.value}/{run_datetime.timeisoformat()}/hfi{for_date_string}.tif'
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'classified.tif')
        classify_hfi(key, temp_filename)
        # threshold 1 = 4k-10k
        # threshold 2 = >10k
        thresholds = [1, 2]
        for threshold in thresholds:
            await process_threshold(threshold, temp_filename, temp_dir, run_parameters_id)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing elevation stats', delta)


async def process_threshold(threshold: int, temp_filename: str, temp_dir: str, run_parameters_id: int):
    threshold_mask_path = create_hfi_threshold_mask(threshold, temp_filename, temp_dir)
    upsampled_threshold_mask_path = upsample_threshold_mask(threshold, threshold_mask_path, temp_dir)
    masked_dem_path = apply_threshold_mask_to_dem(threshold, upsampled_threshold_mask_path, temp_dir)
    await process_elevation_by_firezone(threshold, masked_dem_path, temp_dir, run_parameters_id)

    print('**********')
    print(threshold_mask_path)
    print(upsampled_threshold_mask_path)
    print(masked_dem_path)


def create_hfi_threshold_mask(threshold: int, classified_hfi: str, temp_dir: str):
    target_path = os.path.join(temp_dir, f'hfi_mask_threshold_{threshold}.tif')
    # Read the source data.
    source_tiff = gdal.Open(classified_hfi, gdal.GA_ReadOnly)
    source_band = source_tiff.GetRasterBand(1)
    source_data = source_band.ReadAsArray()
    # Classify the data according to the given threshold
    classified = np.where(source_data == threshold, threshold, 0)

    # Remove any existing target file.
    if os.path.exists(target_path):
        os.remove(target_path)
    output_driver = gdal.GetDriverByName("GTiff")
    # Create an object with the same dimensions as the input, but with 8 bit unsigned values.
    target_tiff = output_driver.Create(target_path, xsize=source_band.XSize,
                                       ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
    # Set the geotransform and projection to the same as the input.
    target_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
    target_tiff.SetProjection(source_tiff.GetProjection())

    # Write the classified data to the band.
    target_band = target_tiff.GetRasterBand(1)
    target_band.SetNoDataValue(0)
    target_band.WriteArray(classified)
    target_tiff = None
    return target_path


def upsample_threshold_mask(threshold: int, source_path: str, temp_dir: str):
    upsampled_threshold_mask_path = os.path.join(temp_dir, f'upsampled_threshold_{threshold}_mask.tif')
    dem = gdal.Open(DEM_PATH, gdal.GA_ReadOnly)
    geo_transform = dem.GetGeoTransform()
    x_res = geo_transform[1]
    y_res = -geo_transform[5]
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * dem.RasterXSize
    miny = maxy + geo_transform[5] * dem.RasterYSize
    extent = [minx, miny, maxx, maxy]
    gdal.Warp(target_path, source_path, outputBounds=extent,
              xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)
    dem = None
    return upsampled_threshold_mask_path


def apply_threshold_mask_to_dem(threshold: int, mask_path: str, temp_dir: str):
    masked_dem_path = os.path.join(temp_dir, f'masked_dem_threshold_{threshold}.tif')
    dem = gdal.Open(DEM_PATH, gdal.GA_ReadOnly)
    dem_band = dem.GetRasterBand(1)
    dem_data = dem_band.ReadAsArray()
    mask = gdal.Open(mask_path, gdal.GA_ReadOnly)
    mask_data = mask.GetRasterBand(1).ReadAsArray()
    masked_dem_data = np.multiply(dem_data, mask_data)
    output_driver = gdal.GetDriverByName("GTiff")
    masked_dem = output_driver.Create(masked_dem_path, xsize=dem_band.XSize,
                                      ysize=dem_band.YSize, bands=1, eType=gdal.GDT_Int16)
    masked_dem.SetGeoTransform(dem.GetGeoTransform())
    masked_dem.SetProjection(dem.GetProjection())
    masked_dem_band = masked_dem.GetRasterBand(1)
    masked_dem_band.SetNoDataValue(0)
    masked_dem_band.WriteArray(masked_dem_data)
    # masked_dem_band.FlushCache()
    dem = None
    mask = None
    masked_dem = None
    return masked_dem_path


async def process_elevation_by_firezone(threshold: int, masked_dem_path: str, temp_dir: str, run_parameters_id: int):
    async with get_async_read_session_scope() as session:
        stmt = 'SELECT id, source_identifier FROM advisory_shapes;'
        result = await session.execute(stmt)
        rows = result.all()
        for row in rows:
            firezone_elevation_threshold_path = intersect_raster_by_firezone(
                threshold, row[0], row[1], masked_dem_path, temp_dir)
            stats = get_elevation_stats(firezone_elevation_threshold_path)
            store_elevation_stats(threshold, row[0], stats, run_parameters_id)


def intersect_raster_by_firezone(threshold: int, id: int, source_identifier: str, raster_path: str, temp_dir: str):
    output_path = os.path.join(temp_dir, f'firezone_{source_identifier}_threshold_{threshold}.tif')
    warp_options = gdal.WarpOptions(
        format="GTiff",
        cutlineDSName=DB_READ_STRING,
        cutlineSQL=f"SELECT geom FROM advisory_shapes WHERE id={id}",
        cropToCutline=True
    )
    gdal.Warp(output_path, raster_path, options=warp_options)
    return output_path


def get_elevation_stats(source_path: str):
    source = gdal.Open(source_path, gdal.GA_ReadOnly)
    source_band = source.GetRasterBand(1)
    stats = source_band.GetStatistics(True, True)
    return {
        'min': stats[0],
        'max': stats[1]
    }


def store_elevation_stats(threshold: int, shape_id: int, stats, run_parameters_id):
    print()


# async def process_elevation_distribution(classified_hfi):
#     with tempfile.TemporaryDirectory() as temp_dir:
#         temp_dir = TEMP_PATH
#         mask_4k_path = os.path.join(temp_dir, 'mask_4k.tif')
#         upsampled_4k_path = os.path.join(temp_dir, 'upsampled_4k.tif')
#         dem_masked_4k = os.path.join(temp_dir, 'dem_masked_4k.tif')
#         # create_mask(mask_4k_path, classified_hfi, 1)
#         # create_mask(mask_10k_path, classified_hfi, 2)
#         # upsample_hfi_mask(mask_4k_path, upsampled_4k_path)
#         # apply_dem_mask(upsampled_4k_path, dem_masked_4k)

#         async with get_async_read_session_scope() as session:
#             stmt = 'SELECT id, source_identifier FROM advisory_shapes;'
#             result = await session.execute(stmt)
#             rows = result.all()
#             for row in rows:
#                 intersect_raster_by_firezone(row[0], row[1], DEM_PATH, DEM_OUTPUT_PATH)
#         get_raster_stats('/Users/dareboss/Documents/elevation/dem/firezone_401.tif')
#     print('Done!!!')


# def create_mask(target_path, classified_hfi, threshold):
#     # Read the source data.
#     source_tiff = gdal.Open(classified_hfi, gdal.GA_ReadOnly)
#     source_band = source_tiff.GetRasterBand(1)
#     source_data = source_band.ReadAsArray()
#     # Classify the data.
#     classified = np.where(source_data == threshold, threshold, 0)

#     # Remove any existing target file.
#     if os.path.exists(target_path):
#         os.remove(target_path)
#     output_driver = gdal.GetDriverByName("GTiff")
#     # Create an object with the same dimensions as the input, but with 8 bit unsigned values.
#     target_tiff = output_driver.Create(target_path, xsize=source_band.XSize,
#                                        ysize=source_band.YSize, bands=1, eType=gdal.GDT_Byte)
#     # Set the geotransform and projection to the same as the input.
#     target_tiff.SetGeoTransform(source_tiff.GetGeoTransform())
#     target_tiff.SetProjection(source_tiff.GetProjection())

#     # Write the classified data to the band.
#     target_band = target_tiff.GetRasterBand(1)
#     target_band.SetNoDataValue(0)
#     target_band.WriteArray(classified)
#     target_tiff = None
