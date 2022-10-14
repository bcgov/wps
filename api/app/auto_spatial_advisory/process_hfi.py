""" Code relating to processing HFI GeoTIFF files, and storing resultant data.
"""
import logging
import os
from enum import Enum
from datetime import date
from time import perf_counter
import tempfile
from shapely import wkb, wkt
from shapely.validation import make_valid
from osgeo import ogr, osr
from app import config
from app.db.models.auto_spatial_advisory import ClassifiedHfi, HfiClassificationThreshold, RunTypeEnum
from app.db.database import get_async_read_session_scope, get_async_write_session_scope
from app.db.crud.auto_spatial_advisory import (
    save_hfi, get_hfi_classification_threshold, HfiClassificationThresholdEnum)
from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.polygonize import polygonize_in_memory
from app.geospatial import NAD83_BC_ALBERS


logger = logging.getLogger(__name__)


class RunType(Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'


class UnknownHFiClassification(Exception):
    """ Raised when the hfi classification is not one of the expected values. """


def create_model_object(feature: ogr.Feature,
                        advisory: HfiClassificationThreshold,
                        warning: HfiClassificationThreshold,
                        coordinate_transform: osr.CoordinateTransformation,
                        run_type: RunType,
                        run_date: date,
                        for_date: date) -> ClassifiedHfi:
    hfi = feature.GetField(0)
    if hfi == 1:
        threshold_id = advisory.id
    elif hfi == 2:
        threshold_id = warning.id
    else:
        raise UnknownHFiClassification(f'unknown hfi value: {hfi}')
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
    return ClassifiedHfi(threshold=threshold_id,
                         run_type=RunTypeEnum(run_type.value),
                         run_date=run_date,
                         for_date=for_date,
                         geom=wkb.dumps(polygon,
                                        hex=True,
                                        srid=NAD83_BC_ALBERS))


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

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing HFI', delta)
