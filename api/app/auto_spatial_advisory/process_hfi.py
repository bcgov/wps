""" Code relating to processing HFI GeoTIFF files, and storing resultant data.
"""
# pylint: skip-file
import logging
import os
from datetime import date, datetime
from time import perf_counter
import tempfile
from shapely import wkb, wkt
from shapely.validation import make_valid
from shapely.geometry import MultiPolygon
from osgeo import ogr, osr
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.auto_spatial_advisory.common import get_s3_key
from app.db.models.auto_spatial_advisory import ClassifiedHfi, HfiClassificationThreshold, RunTypeEnum, HighHfiArea
from app.db.database import get_async_read_session_scope, get_async_write_session_scope, get_sync_tileserv_db_scope
from app.db.crud.auto_spatial_advisory import (
    save_hfi, get_hfi_classification_threshold, HfiClassificationThresholdEnum, save_run_parameters,
    get_run_parameters_id, calculate_high_hfi_areas, save_high_hfi_area)
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.elevation import process_elevation
from app.auto_spatial_advisory.polygonize import polygonize_in_memory
from app.auto_spatial_advisory.run_type import RunType
from app.geospatial import NAD83_BC_ALBERS


logger = logging.getLogger(__name__)


class UnknownHFiClassification(Exception):
    """ Raised when the hfi classification is not one of the expected values. """


def write_classified_hfi_to_tileserver(session: Session,
                                       feature: ogr.Feature,
                                       coordinate_transform: osr.CoordinateTransformation,
                                       for_date: date,
                                       run_datetime: datetime,
                                       run_type: RunType,
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
        'INSERT INTO hfi (hfi, for_date, run_date, run_type, geom) VALUES (:hfi, :for_date, :run_date, :run_type, ST_GeomFromText(:geom, 3005))')
    session.execute(statement, {'hfi': threshold.description, 'for_date': for_date,
                    'run_date': run_datetime, 'run_type': run_type.value, 'geom': wkt.dumps(polygon)})
    session.commit()


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
                        run_datetime: datetime,
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
                         run_datetime=run_datetime,
                         for_date=for_date,
                         geom=wkb.dumps(polygon,
                                        hex=True,
                                        srid=NAD83_BC_ALBERS))


async def write_high_hfi_area(session: AsyncSession, row: any, run_parameters_id: int):
    high_hfi_area = HighHfiArea(advisory_shape_id=row.shape_id,
                                run_parameters=run_parameters_id,
                                area=row.area,
                                threshold=row.threshold)
    await save_high_hfi_area(session, high_hfi_area)


async def process_hfi(run_type: RunType, run_date: date, run_datetime: datetime, for_date: date):
    """ Create a new hfi record for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_date: The date of the run to process. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    # Skip if we already have this run
    async with get_async_read_session_scope() as session:
        existing_run = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        if existing_run is not None:
            logger.info(
                (
                    f'Skipping run, already processed for run_type:{run_type}'
                    f'run_datetime:{run_datetime},'
                    f'for_date:{for_date}'
                ))
            return

    logger.info('Processing HFI %s for run date: %s, for date: %s', run_type, run_date, for_date)
    perf_start = perf_counter()

    key = get_s3_key(run_type, run_date, for_date)
    logger.info(f'Key to HFI in object storage: {key}')
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'classified.tif')
        classify_hfi(key, temp_filename)
        with polygonize_in_memory(temp_filename) as layer:

            spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
            target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

            async with get_async_write_session_scope() as session:
                advisory = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.ADVISORY)
                warning = await get_hfi_classification_threshold(session, HfiClassificationThresholdEnum.WARNING)

                logger.info('Writing HFI advisory zones to API database...')
                for i in range(layer.GetFeatureCount()):
                    # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Feature
                    feature: ogr.Feature = layer.GetFeature(i)
                    obj = create_model_object(feature,
                                              advisory,
                                              warning,
                                              coordinate_transform,
                                              run_type,
                                              run_datetime,
                                              for_date)
                    await save_hfi(session, obj)

                run_parameters_id = await get_run_parameters_id(session, run_type, run_date, for_date)

                logger.info('Getting high HFI area per zone...')
                high_hfi_areas = await calculate_high_hfi_areas(session, run_parameters_id)

                logger.info('Writing high HFI areas...')
                for row in high_hfi_areas:
                    await write_high_hfi_area(session, row, run_parameters_id)

                # Store the unqiue combination of run type, run datetime and for date in the run_parameters table
                await save_run_parameters(session, run_type, run_datetime, for_date)

                with get_sync_tileserv_db_scope() as session:
                    logger.info('Writing HFI vectors to tileserv...')
                    for i in range(layer.GetFeatureCount()):
                        feature: ogr.Feature = layer.GetFeature(i)
                        write_classified_hfi_to_tileserver(
                            session, feature, coordinate_transform, for_date, run_datetime, run_type, advisory, warning)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing HFI', delta)
