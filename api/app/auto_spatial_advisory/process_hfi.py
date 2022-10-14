""" Code relating to processing HFI GeoTIFF files, and storing resultant data.
"""
# pylint: skip-file
import logging
import os
from enum import Enum
from datetime import date
from time import perf_counter
import tempfile
from shapely import wkb, wkt
from shapely.validation import make_valid
from shapely.geometry import MultiPolygon
import tempfile
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.auto_spatial_advisory.db.database.tileserver import get_tileserver_write_session_scope
from app.auto_spatial_advisory.sfms import get_prefix, get_target_filename
from osgeo import ogr, osr, gdal
from app import config
from app.db.models.auto_spatial_advisory import ClassifiedHfi, HfiClassificationThreshold, RunTypeEnum
from app.db.database import get_async_read_session_scope, get_async_write_session_scope
from app.db.crud.auto_spatial_advisory import (
    save_hfi, get_hfi_classification_threshold, HfiClassificationThresholdEnum)
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.polygonize import polygonize_in_memory
from app.geospatial import NAD83_BC_ALBERS
from app.routers.sfms import FileLikeObject
from app.utils.s3 import get_client
from app.utils.time import get_vancouver_now


logger = logging.getLogger(__name__)


class RunType(Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'

    @staticmethod
    def from_str(label):
        if label in ('forecast', 'Forecast', 'FORECAST'):
            return RunType.FORECAST
        elif label in ('actual', 'Actual', 'ACTUAL'):
            return RunType.ACTUAL
        else:
            raise NotImplementedError


class UnknownHFiClassification(Exception):
    """ Raised when the hfi classification is not one of the expected values. """


async def write_classified_hfi_to_tileserver(session: AsyncSession,
                                             feature: ogr.Feature,
                                             coordinate_transform: osr.CoordinateTransformation,
                                             date: date,
                                             advisory: HfiClassificationThreshold,
                                             warning: HfiClassificationThreshold):
    """
    Given an ogr.Feature with an assigned HFI threshold value, write it to the tileserv database as a vector.
    """
    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Geometry
    geometry: ogr.Geometry = feature.GetGeometryRef()
    # Make sure the geometry is in target_srs!
    geometry.Transform(coordinate_transform)
    # Would be very nice to go directly from the ogr.Geometry into the database,
    # but Sybrand can't figure out how to have the wkt output also include the fact that
    # the SRID is target_srs. So we're doing this redundant step of creating a shapely
    # geometry from wkt, then dumping it back into wkb, with target srid.
    # NOTE: geometry.ExportToIsoWkb isn't consistent in it's return value between
    # different versions of gdal (bytearray vs. bytestring) - so we're opting for
    # wkt instead of wkb here for better compatibility.
    polygon = wkt.loads(geometry.ExportToIsoWkt())
    polygon = make_valid(polygon)
    polygon = MultiPolygon([polygon])

    threshold = get_threshold_from_hfi(feature, advisory, warning)

    statement = text(
        'INSERT INTO hfi (hfi, date, geom) VALUES (:hfi, :date, ST_GeomFromText(:geom, 3005))')
    await session.execute(statement, {'hfi': threshold.description, 'date': date, 'geom': wkt.dumps(polygon)})


def get_threshold_from_hfi(feature: ogr.Feature, advisory: HfiClassificationThreshold, warning: HfiClassificationThreshold):
    """
    Parses the HFI id value (1 or 2) attributed to an ogr.Feature, and returns the id of the
    appropriate HfiClassificationThreshold record in the database.
    """
    hfi = feature.GetField(0)
    if hfi == 1:
        return advisory
    elif hfi == 2:
        return warning
    else:
        raise UnknownHFiClassification(f'unknown hfi value: {hfi}')


def create_model_object(feature: ogr.Feature,
                        advisory: HfiClassificationThreshold,
                        warning: HfiClassificationThreshold,
                        coordinate_transform: osr.CoordinateTransformation,
                        run_type: RunType,
                        run_date: date,
                        for_date: date) -> ClassifiedHfi:
    threshold = get_threshold_from_hfi(feature, advisory, warning)
    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Geometry
    geometry: ogr.Geometry = feature.GetGeometryRef()
    # Make sure the geometry is in EPSG:3005!
    geometry.Transform(coordinate_transform)
    # Would be very nice to go directly from the ogr.Geometry into the database,
    # but I can't figure out how to have the wkt output also include the fact that
    # the SRID is EPSG:3005. So we're doing this redundant step of creating a shapely
    # geometry from wkt, then dumping it back into wkb, with srid=3005.
    # NOTE: geometry.ExportToIsoWkb isn't consistent in it's return value between
    # different versions of gdal (bytearray vs. bytestring) - so we're opting for
    # wkt instead of wkb here for better compatibility.
    polygon = wkt.loads(geometry.ExportToIsoWkt())
    polygon = make_valid(polygon)
    return ClassifiedHfi(threshold=threshold.id,
                         run_type=RunTypeEnum(run_type.value),
                         run_date=run_date,
                         for_date=for_date,
                         geom=wkb.dumps(polygon,
                                        hex=True,
                                        srid=NAD83_BC_ALBERS))


def get_target_filename(run_type: RunType, run_date: date, for_date_str: str) -> str:
    """ Get the target filename, something that looks like this:
    bucket/sfms/cog/forecast/[issue date NOT TIME]/cog_hfi20220823.tif
    bucket/sfms/cog/actual/[issue date NOT TIME]/cog_hfi20220823.tif
    """
    # create the filename
    return os.path.join('sfms', 'cog', run_type.value, run_date.isoformat()[:10], 'cog_hfi' + for_date_str + '.tif')


async def create_cloud_optimized_raster(classified_hfi_filepath, run_type: RunType, run_date: date, for_date_str: str):
    """
    Uses gdal tools to create a cloud-optimized raster of the classified HFI
    """
    dest_filename = "cog_hfi{}.tif".format(for_date_str)
    temp_filename = 'tmp.tif'
    logger.info(
        f'Creating Cloud Optimized Geotiff {dest_filename} for {run_type.value}/{run_date.isoformat()}/{for_date_str}')

    source_tiff = gdal.Open(classified_hfi_filepath, gdal.GA_ReadOnly)

    translate_options = gdal.TranslateOptions(format='GTiff', creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'])
    dataset = gdal.Translate(temp_filename, source_tiff, options=translate_options)

    # rebuild overview image
    # (This is the python equivalent of gdaladdo - splits the source dataset into smaller pieces)
    dataset.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64])

    # create COG
    driver = gdal.GetDriverByName('GTiff')
    driver.CreateCopy(dest_filename, dataset, options=[
        "COPY_SRC_OVERVIEWS=YES", "TILED=YES", "COMPRESS=LZW"])

    # upload COG file to object store
    key = get_target_filename(run_type, run_date, for_date_str)
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        with open(dest_filename, 'rb') as f:
            logger.info('Uploading file to "%s"', key)
            await client.put_object(Bucket=bucket,
                                    Key=key,
                                    Body=FileLikeObject(f))
        f.close()
        logger.info('Done uploading file')

    del dataset
    del driver


async def process_hfi(run_type: RunType, run_date: date, for_date: date):
    """ Create a new hfi record for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info('Processing HFI %s for run date: %s, for date: %s', run_type, run_date, for_date)
    perf_start = perf_counter()

    bucket = config.get('OBJECT_STORE_BUCKET')
    # TODO what really has to happen, is that we grab the most recent prediction for the given date,
    # but this method doesn't even belong here, it's just a shortcut for now!
    for_date_string = f'{for_date.year}{for_date.month:02d}{for_date.day:02d}'

    # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    key = f'/vsis3/{bucket}/sfms/uploads/{run_type.value}/{run_date.isoformat()}/hfi{for_date_string}.tif'
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'classified.tif')
        classify_hfi(key, temp_filename)
        with polygonize_in_memory(temp_filename) as layer:

            spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
            target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

            async with get_async_read_session_scope() as session:
                advisory = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.ADVISORY)
                warning = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.WARNING)

            async with get_async_write_session_scope() as session:
                for i in range(layer.GetFeatureCount()):
                    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Feature
                    feature: ogr.Feature = layer.GetFeature(i)
                    obj = create_model_object(feature,
                                              advisory,
                                              warning,
                                              coordinate_transform,
                                              run_type,
                                              run_date,
                                              for_date)
                    await save_hfi(session, obj)

            async with get_tileserver_write_session_scope() as session:
                logger.info('Writing HFI vectors to tileserv...')
                for i in range(layer.GetFeatureCount()):
                    feature: ogr.Feature = layer.GetFeature(i)
                    await write_classified_hfi_to_tileserver(session, feature, coordinate_transform, for_date, advisory, warning)

            await create_cloud_optimized_raster(temp_filename, run_type, run_date, for_date_string)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing HFI', delta)
