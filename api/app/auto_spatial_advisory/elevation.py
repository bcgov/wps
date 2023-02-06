""" Takes a classified HFI image and calculates basic elevation statistics associated with advisory areas per fire zone.
"""

from datetime import date, datetime
from time import perf_counter
import logging
import os
import tempfile
import numpy as np
from osgeo import gdal
from app import config
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.run_type import RunType
from app.db.crud.auto_spatial_advisory import get_run_parameters_id, save_advisory_elevation_stats
from app.db.database import get_async_read_session_scope, get_async_write_session_scope, DB_READ_STRING
from app.db.models.auto_spatial_advisory import AdvisoryElevationStats
from app.utils.s3 import get_client


logger = logging.getLogger(__name__)
DEM_GDAL_SOURCE = None


async def process_elevation(source_path: str, run_type: RunType, run_datetime: datetime, for_date: date):
    """ Create new elevation statistics records for the given parameters.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    logger.info('Processing elevation stats %s for run date: %s, for date: %s', run_type, run_datetime, for_date)
    perf_start = perf_counter()

    # Get the id from run_parameters associated with the provided runtype, for_date and for_datetime
    async with get_async_read_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

        # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
        # it's S3 virtual file system driver to read the file.
        # https://gdal.org/user/virtual_file_systems.html
        with tempfile.TemporaryDirectory() as temp_dir:
            await prepare_dem()
            temp_filename = os.path.join(temp_dir, 'classified.tif')
            classify_hfi(source_path, temp_filename)
            # thresholds: 1 = 4k-10k, 2 = >10k
            thresholds = [1, 2]
            for threshold in thresholds:
                await process_threshold(threshold, temp_filename, temp_dir, run_parameters_id)

        perf_end = perf_counter()
        delta = perf_end - perf_start
        logger.info('%f delta count before and after processing elevation stats', delta)
        global DEM_GDAL_SOURCE  # pylint: disable=global-statement
        DEM_GDAL_SOURCE = None


async def prepare_dem():
    """
    Fetches a dem from S3 storage, opens it with gdal and assigns it to a global variable
    for use in other functions. This is a little clunky, but we only want to grab the dem from
    object storage once because it is a slow process.
    """
    async with get_client() as (client, bucket):
        dem = await client.get_object(Bucket=bucket, Key=f'dem/mosaics/{config.get("DEM_NAME")}')
        mem_path = '/vsimem/dem.tif'
        data = await dem['Body'].read()
        gdal.FileFromMemBuffer(mem_path, data)
        global DEM_GDAL_SOURCE  # pylint: disable=global-statement
        DEM_GDAL_SOURCE = gdal.Open(mem_path, gdal.GA_ReadOnly)
        gdal.Unlink(mem_path)


async def process_threshold(threshold: int, source_path: str, temp_dir: str, run_parameters_id: int):
    """
    Step-by-step processing to extract elevation stats per advisory type per fire zone.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param source_path: A HFI tif that is classified with 0 = < 4k, 1 = 4k-10k, 2 = > 10k
    :param temp_dir: A temporary location for storing intermediate files
    :param run_parameters_id: The RunParameter object id associated with this run_type, for_date and run_datetime
    """
    threshold_mask_path = create_hfi_threshold_mask(threshold, source_path, temp_dir)
    upsampled_threshold_mask_path = upsample_threshold_mask(threshold, threshold_mask_path, temp_dir)
    masked_dem_path = apply_threshold_mask_to_dem(threshold, upsampled_threshold_mask_path, temp_dir)
    await process_elevation_by_firezone(threshold, masked_dem_path, run_parameters_id)


def create_hfi_threshold_mask(threshold: int, classified_hfi: str, temp_dir: str):
    """
    Creates a mask from a classified HFI tif wherein pixels that match the threshold are assigned a value of 1 and
    all other pixels = 0.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param classified_hfi: The path to the classified HFI tif
    :param temp_dir: A temporary location for storing intermediate files
    """
    target_path = os.path.join(temp_dir, f'hfi_mask_threshold_{threshold}.tif')
    # Read the source data.
    source_tiff = gdal.Open(classified_hfi, gdal.GA_ReadOnly)
    source_band = source_tiff.GetRasterBand(1)
    source_data = source_band.ReadAsArray()
    # Classify the data according to the given threshold
    classified = np.where(source_data == threshold, 1, 0)

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
    """
    Increases the resolution of the masked HFI tif to match the DEM. This step is required in order to use raster
    algebra to multiply the DEM by the output mask.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param source_path: The path to the mask tif that needs to be upsampled
    :param temp_dir: A temporary location for storing intermediate files
    """
    upsampled_threshold_mask_path = os.path.join(temp_dir, f'upsampled_threshold_{threshold}_mask.tif')
    geo_transform = DEM_GDAL_SOURCE.GetGeoTransform()
    x_res = geo_transform[1]
    y_res = -geo_transform[5]
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * DEM_GDAL_SOURCE.RasterXSize
    miny = maxy + geo_transform[5] * DEM_GDAL_SOURCE.RasterYSize
    extent = [minx, miny, maxx, maxy]
    gdal.Warp(upsampled_threshold_mask_path, source_path, outputBounds=extent,
              xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)
    return upsampled_threshold_mask_path


def apply_threshold_mask_to_dem(threshold: int, mask_path: str, temp_dir: str):
    """
    Multiplies the mask of HFI areas by the DEM. The resulting tif has elevation values at pixels where HFI exceeds the
    specified threshold, all other pixels are 0.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param mask_path: The path to the mask tif
    :param temp_dir: A temporary location for storing intermediate files
    """
    masked_dem_path = os.path.join(temp_dir, f'masked_dem_threshold_{threshold}.tif')
    dem_band = DEM_GDAL_SOURCE.GetRasterBand(1)
    dem_data = dem_band.ReadAsArray()
    mask = gdal.Open(mask_path, gdal.GA_ReadOnly)
    mask_data = mask.GetRasterBand(1).ReadAsArray()
    masked_dem_data = np.multiply(dem_data, mask_data)
    output_driver = gdal.GetDriverByName("GTiff")
    masked_dem = output_driver.Create(masked_dem_path, xsize=dem_band.XSize,
                                      ysize=dem_band.YSize, bands=1, eType=gdal.GDT_Int16)
    masked_dem.SetGeoTransform(DEM_GDAL_SOURCE.GetGeoTransform())
    masked_dem.SetProjection(DEM_GDAL_SOURCE.GetProjection())
    masked_dem_band = masked_dem.GetRasterBand(1)
    masked_dem_band.SetNoDataValue(0)
    masked_dem_band.WriteArray(masked_dem_data)
    mask = None
    masked_dem = None
    return masked_dem_path


async def process_elevation_by_firezone(threshold: int, masked_dem_path: str, run_parameters_id: int):
    """
    Given a tif that only contains elevations values at pixels where HFI exceeds the threshold, calculate statistics
    and store them in the API database.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param mask_dem_path: The path to the dem that has had the upsampled hfi mask applied
    :param run_parameters_id: The RunParameter object id associated with this run_type, for_date and run_datetime
    """
    async with get_async_read_session_scope() as session:
        stmt = 'SELECT id, source_identifier FROM advisory_shapes;'
        result = await session.execute(stmt)
        rows = result.all()
        for row in rows:
            # using a temp dir here to prevent accumulation of large rasters as we run through this loop
            with tempfile.TemporaryDirectory() as temp_dir:
                firezone_elevation_threshold_path = intersect_raster_by_firezone(threshold, row[0], row[1],
                                                                                 masked_dem_path, temp_dir)
                stats = get_elevation_stats(firezone_elevation_threshold_path)
                await store_elevation_stats(threshold, row[0], stats, run_parameters_id)


def intersect_raster_by_firezone(threshold: int, advisory_shape_id: int, source_identifier: str, raster_path: str,
                                 temp_dir: str):
    """
    Given a raster and a fire zone id, use gdal.Warp to clip out a fire zone from which we can retrieve stats.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param advisory_shape_id: The id of the fire zone (aka advisory_shape object) to clip with
    :param source_identifier: The source identifer of the fire zone.
    :param raster_path: The path to the raster to be clipped.
    :param temp_dir: A temporary location for storing intermediate files
    """
    output_path = os.path.join(temp_dir, f'firezone_{source_identifier}_threshold_{threshold}.tif')
    warp_options = gdal.WarpOptions(
        format="GTiff",
        cutlineDSName=DB_READ_STRING,
        cutlineSQL=f"SELECT geom FROM advisory_shapes WHERE id={advisory_shape_id}",
        cropToCutline=True
    )
    gdal.Warp(output_path, raster_path, options=warp_options)
    return output_path


def get_elevation_stats(source_path: str):
    """
    Extracts basic statistics from a raster.

    :param source_path: The path to the raster of interest.
    """
    source = gdal.Open(source_path, gdal.GA_ReadOnly)
    source_band = source.GetRasterBand(1)
    source_data = source_band.ReadAsArray()
    max_elevation = np.max(source_data)
    if max_elevation == 0:
        median = 0
        minimum = 0
        maximum = 0
        quartile_25 = 0
        quartile_75 = 0
    else:
        median = np.median(source_data[source_data != 0])
        minimum = np.min(source_data[source_data != 0])
        maximum = np.max(source_data[source_data != 0])
        quartile_25 = np.percentile(source_data[source_data != 0], 25)
        quartile_75 = np.percentile(source_data[source_data != 0], 75)
    return {
        'minimum': minimum,
        'maximum': maximum,
        'median': median,
        'quartile_25': quartile_25,
        'quartile_75': quartile_75
    }


async def store_elevation_stats(threshold: int, shape_id: int, stats, run_parameters_id):
    """
    Writes elevation statistics to the API database.
    TODO - We should probably save up a list of objects to add to the database and only call this function once
    per threhold.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k
    :param shape_id: The advisory shape id.
    :param run_parameters_id: The RunParameter object id associated with this run_type, for_date and run_datetime
    """
    advisory_elevation_stats = AdvisoryElevationStats(advisory_shape_id=shape_id, minimum=stats['minimum'],
                                                      maximum=stats['maximum'], median=stats['median'],
                                                      quartile_25=stats['quartile_25'],
                                                      quartile_75=stats['quartile_75'],
                                                      run_parameters=run_parameters_id, threshold=threshold)
    async with get_async_write_session_scope() as session:
        await save_advisory_elevation_stats(session, advisory_elevation_stats)
