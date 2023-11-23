""" Code relating to processing high HFI area per fire zone
"""

import logging
import numpy as np
import os
import tempfile
from datetime import date, datetime
from osgeo import gdal
from time import perf_counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from app import config
from app.auto_spatial_advisory.common import get_s3_key
from app.auto_spatial_advisory.run_type import RunType
from app.db.database import DB_READ_STRING, get_async_write_session_scope
from app.db.models.auto_spatial_advisory import AdvisoryFuelStats, SFMSFuelType
from app.db.crud.auto_spatial_advisory import get_all_hfi_thresholds, get_all_sfms_fuel_types, get_run_parameters_id, save_advisory_fuel_stats


logger = logging.getLogger(__name__)


def get_warped_fuel_type_s3_key():
    """
    Returns the key to the fuel type layer that has been reprojected to the Lambert Conformal Conic spatial reference and
    transformed to match the extent and spatial reference of hfi files output by sfms.
    """
    bucket = config.get("OBJECT_STORE_BUCKET")

    # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    key = f"/vsis3/{bucket}/ftl/fuel_types_lambert_2000.tif"
    return key


def classify_by_threshold(source_data: list[list[float]], threshold: int):
    """
    Classifies the provided 2-d array based on the provided threshold. When the threshold is 1, all cells with an hfi value
    in the range of 4k - 10k are assigned a value of 1 and other cells are assigned a value of 0. When the threshold is 2,
    all cells with an hfi greater than 10k are assigned a value of 1 and other cells are assigned a value of 0.

    :param source_data: A 2-d array with values representing fuel types.
    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    """
    if threshold == 1:
        # advisory
        classified = np.where(source_data < 4000, 0, source_data)
        classified = np.where((classified >= 4000) & (classified < 10000), 1, classified)
        classified = np.where(classified >= 10000, 0, classified)
    else:
        # warning
        classified = np.where(source_data < 10000, 0, source_data)
        classified = np.where(classified >= 10000, 1, classified)
    return classified


async def calculate_fuel_type_area_by_shape(session: AsyncSession, temp_dir: str, source_path: str, threshold, run_parameters_id: int, fuel_types: list[SFMSFuelType]):
    """
    Process masked fuel type layer with each advisory shape (eg fire zone unit).

    :param temp_dir: A temporary location for storing intermediate files.
    :param source_path: Path to the masked fuel type layer.
    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    :param run_parameters_id: The RunParameter object id associated with the run_type, for_date and run_datetime of interest.
    :param fuel_types: A list of fuel types used in the sfms system.
    """
    stmt = text("SELECT id, source_identifier FROM advisory_shapes;")
    result = await session.execute(stmt)
    rows = result.all()
    for row in rows:
        shape_fuel_type_path = intersect_raster_by_advisory_shape(threshold, row[0], row[1], source_path, temp_dir)
        fuel_type_areas = calculate_fuel_type_areas(shape_fuel_type_path, fuel_types)
        await store_advisory_fuel_stats(session, fuel_type_areas, threshold, run_parameters_id, row[0])


async def store_advisory_fuel_stats(session: AsyncSession, fuel_type_areas: dict, threshold: int, run_parameters_id: int, advisory_shape_id: int):
    """
    Creates AdvisoryFuelStats objects and save them in the wps database.

    :param : A dictionary keyed by fuel type code with value representing an area in square meters.
    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    :param run_parameters_id: The RunParameter object id associated with the run_type, for_date and run_datetime of interest.
    :param advisory_shape_id: The id of advisory shape (eg. fire zone unit) the fuel type area has been calcualted for.
    """
    advisory_fuel_stats = []
    for key in fuel_type_areas:
        advisory_fuel_stats.append(
            AdvisoryFuelStats(advisory_shape_id=advisory_shape_id, threshold=threshold, run_parameters=run_parameters_id, fuel_type=key, area=fuel_type_areas[key])
        )
    await save_advisory_fuel_stats(session, advisory_fuel_stats)


def calculate_fuel_type_areas(source_path: str, fuel_types: list[SFMSFuelType]):
    """
    Calculates the ground area of the raster layer at the source_path covered by each fuel type.

    :param source_path: The path to a fuel type layer that has been masked based on hfi value and clipped to an advisory shape.
    :param fuel_types: A list of fuel types from the sfms system that may be present in the source_path fuel type layer.
    """
    source = gdal.Open(source_path, gdal.GA_ReadOnly)
    source_band = source.GetRasterBand(1)
    histogram = source_band.GetHistogram()
    combustible_fuel_type_ids = [fuel_type.fuel_type_id for fuel_type in fuel_types if fuel_type.fuel_type_id < 99 and fuel_type.fuel_type_id > 0]
    fuel_type_areas = {}
    for fuel_type_id in combustible_fuel_type_ids:
        count = histogram[fuel_type_id]
        area = count * 2000 * 2000
        if area > 0:
            fuel_type_areas[fuel_type_id] = area
    return fuel_type_areas


def intersect_raster_by_advisory_shape(threshold: int, advisory_shape_id: int, source_identifier: str, raster_path: str, temp_dir: str):
    """
    Given a raster and a fire shape id, use gdal.Warp to clip out a fire zone from which we can retrieve info.

    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    :param advisory_shape_id: The id of the fire zone (aka advisory_shape object) to clip with.
    :param source_identifier: The source identifer of the advisory shape.
    :param raster_path: The path to the raster to be clipped.
    :param temp_dir: A temporary location for storing intermediate files.
    """
    output_path = os.path.join(temp_dir, f"advisory_shape_{source_identifier}_threshold_{threshold}.tif")
    warp_options = gdal.WarpOptions(format="GTiff", cutlineDSName=DB_READ_STRING, cutlineSQL=f"SELECT geom FROM advisory_shapes WHERE id={advisory_shape_id}", cropToCutline=True)
    gdal.Warp(output_path, raster_path, options=warp_options)
    return output_path


def create_masked_fuel_type_tif(masked_fuel_type_data: list[list[float]], temp_dir: str, threshold: int, geotransform: list[float], projection: str, x_size: int, y_size: int):
    """
    Creates a new raster (a GeoTiff) file using the provided data and parameters.

    :param masked_fuel_type_data: The data to be written to the raster.
    :param temp_dir: A temporary location for storing intermediate files.
    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    :param geotransform: The geotransform of the new raster.
    :param projection: The projection of the new raster.
    :param x_size: The number of pixels in the x direction.
    :param y_size: The number of pixels in the y direction.
    """
    output_driver = gdal.GetDriverByName("GTiff")
    masked_fuel_type_path = os.path.join(temp_dir, f"masked_fuel_type_{threshold}.tif")
    masked_fuel_type = output_driver.Create(masked_fuel_type_path, xsize=x_size, ysize=y_size, bands=1, eType=gdal.GDT_Int16)
    masked_fuel_type.SetGeoTransform(geotransform)
    masked_fuel_type.SetProjection(projection)
    masked_fuel_type_band = masked_fuel_type.GetRasterBand(1)
    masked_fuel_type_band.SetNoDataValue(0)
    masked_fuel_type_band.WriteArray(masked_fuel_type_data)
    masked_fuel_type = None
    return masked_fuel_type_path


async def process_fuel_type_hfi_by_shape(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Entry point for deriving fuel type areas for each hfi threshold per advisory shape (eg. fire zone unit).

    General description of the process:
     - get an hfi raster from S3 based on the run type, run datetime and for date
     - get the fuel type raster from S3
     - for each threshold, create a mask from the hfi raster that will contains values of 0 and 1 for use in raster mulitplication
     - multiply the fuel type layer by the mask in order to filter out fuel types where hfi does not match the threshold
     - for each advisory shape (aka fire zone unit), clip the masked fuel type layer by shape's geometry
     - count the pixels for each fuel type in the clipped fuel type layer to determine the area of each fuel type
     - store the results in the AdvisoryFuelStats table

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    logger.info("Processing fuel type area %s for run date: %s, for date: %s", run_type, run_datetime, for_date)
    perf_start = perf_counter()

    gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", config.get("OBJECT_STORE_SECRET"))
    gdal.SetConfigOption("AWS_ACCESS_KEY_ID", config.get("OBJECT_STORE_USER_ID"))
    gdal.SetConfigOption("AWS_S3_ENDPOINT", config.get("OBJECT_STORE_SERVER"))
    gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

        stmt = select(AdvisoryFuelStats).where(AdvisoryFuelStats.run_parameters == run_parameters_id)
        exists = (await session.execute(stmt)).scalars().first() is not None

        if exists:
            logger.info("Advisory fuel stats already processed")
            return

        # Retrieve the appropriate hfi raster from s3 storage
        hfi_key = get_s3_key(run_type, run_datetime.date(), for_date)
        hfi_raster = gdal.Open(hfi_key, gdal.GA_ReadOnly)
        hfi_data = hfi_raster.GetRasterBand(1).ReadAsArray()

        # Retrieve the fuel type raster from s3 storage. This raster has previously been reprojected to a
        # Lambert Confirmal Conic spatial reference and re-sampled to match the extent and resolution
        # of the hfi rasters we get from sfms
        fuel_type_key = get_warped_fuel_type_s3_key()
        fuel_type_raster = gdal.Open(fuel_type_key, gdal.GA_ReadOnly)
        fuel_type_band = fuel_type_raster.GetRasterBand(1)
        fuel_type_data = fuel_type_band.ReadAsArray()

        # Properties useful for creating a new GeoTiff
        geotransform = fuel_type_raster.GetGeoTransform()
        projection = fuel_type_raster.GetProjection()
        x_size = fuel_type_band.XSize
        y_size = fuel_type_band.YSize

        thresholds = await get_all_hfi_thresholds(session)
        fuel_types = await get_all_sfms_fuel_types(session)

        with tempfile.TemporaryDirectory() as temp_dir:
            for threshold in thresholds:
                classified_hfi_data = classify_by_threshold(hfi_data, threshold.id)
                masked_fuel_type_data = np.multiply(fuel_type_data, classified_hfi_data)
                masked_fuel_type_path = create_masked_fuel_type_tif(masked_fuel_type_data, temp_dir, threshold.id, geotransform, projection, x_size, y_size)
                await calculate_fuel_type_area_by_shape(session, temp_dir, masked_fuel_type_path, threshold.id, run_parameters_id, fuel_types)
    # Clean up open gdal objects
    hfi_raster = None
    fuel_type_raster = None

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after processing fuel type area by hfi per fire shape", delta)
