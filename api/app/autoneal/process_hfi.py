import logging
import os
from datetime import date
from time import perf_counter
import tempfile
from shapely import wkb
from osgeo import ogr, osr
from app import config
from app.db.models.advisory import ClassifiedHfi
from app.db.database import get_async_write_session_scope
from app.db.crud.fba_advisory import save_hfi
from app.autoneal.classify_hfi import classify_hfi
from app.autoneal.polygonize import polygonize


logger = logging.getLogger(__name__)


async def process_hfi(for_date: date):
    """ Create a new hfi record for the given date.
    TODO: this doesn't belong in the router! but where???
    """
    logger.info('Processing HFI for %s', for_date)
    perf_start = perf_counter()

    bucket = config.get('OBJECT_STORE_BUCKET')
    # TODO what really has to happen, is that we grab the most recent prediction for the given date,
    # but this method doesn't even belong here, it's just a shortcut for now!
    run_date = for_date
    for_date_string = f'{for_date.year}{for_date.month:02d}{for_date.day:02d}'

    key = f'/vsis3/{bucket}/sfms/uploads/forecast/{run_date.isoformat()}/hfi{for_date_string}.tif'
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_filename = os.path.join(temp_dir, 'classified.tif')
        classify_hfi(key, temp_filename)
        dst_ds, layer = polygonize(temp_filename)

        spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(3005)
        coordinateTransform = osr.CoordinateTransformation(spatial_reference, target_srs)

        async with get_async_write_session_scope() as session:
            for i in range(layer.GetFeatureCount()):
                # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Feature
                feature: ogr.Feature = layer.GetFeature(i)
                hfi = feature.GetField(0)
                if hfi == 1:
                    hfi = '4000 < hfi < 10000'
                elif hfi == 2:
                    hfi = 'hfi >= 10000'
                else:
                    raise Exception('unknown hfi value!')
                # https://gdal.org/api/python/osgeo.ogr.html#osgeo.ogr.Geometry
                geometry: ogr.Geometry = feature.GetGeometryRef()
                # Make sure the geometry is in 3005!
                geometry.Transform(coordinateTransform)
                # Would be very nice to go directly from the ogr.Geometry into the database,
                # but I can't figure out how to have the wkt output also include the fact that
                # the SRID is 3005. So we're doing this redundant step of creating a shapely
                # geometry from wkb, then dumping it back into wkb, with srid=3005.
                polygon = wkb.loads(geometry.ExportToIsoWkb())
                obj = ClassifiedHfi(hfi=hfi, date=for_date, geom=wkb.dumps(polygon, hex=True, srid=3005))
                await save_hfi(session, obj)
        del dst_ds, layer
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after processing HFI', delta)
