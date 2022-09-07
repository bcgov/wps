""" Routers for new/formal/non-tinker fba.
"""
import os
import logging
from datetime import date
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
import tempfile
from shapely import wkb
from osgeo import ogr, osr
from app import config
from app.db.database import get_async_read_session_scope, get_async_write_session_scope
from app.db.crud.fba_advisory import get_hfi_area_percentages, get_hfi, save_hfi
from app.db.models.advisory import ClassifiedHfi
from app.auth import authentication_required, audit
from app.schemas.fba import FireCenterListResponse, FireZoneAreaListResponse, FireZoneArea
from app.wildfire_one.wfwx_api import (get_auth_header, get_fire_centers)
from app.autoneal.classify_hfi import classify_hfi
from app.autoneal.polygonize_hfi import polygonize

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    # dependencies=[Depends(authentication_required), Depends(audit)],
)


async def process_hfi(for_date: date):
    """ Create a new hfi record for the given date.
    TODO: this doesn't belong in the router! but where???
    """
    logger.info('Processing HFI for %s', for_date)
    async with get_async_write_session_scope() as session:
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


@router.get('/fire-centers', response_model=FireCenterListResponse)
async def get_all_fire_centers(_=Depends(authentication_required)):
    """ Returns fire centers for all active stations. """
    logger.info('/fba/fire-centers/')
    async with ClientSession() as session:
        header = await get_auth_header(session)
        fire_centers = await get_fire_centers(session, header)
    return FireCenterListResponse(fire_centers=fire_centers)


@router.get('/fire-zone-areas/{for_date}', response_model=FireZoneAreaListResponse)
# async def get_zones(for_date: date, _=Depends(authentication_required)):
async def get_zones(for_date: date):
    async with get_async_read_session_scope() as session:
        zones = []

        # this is a slow step! checking to see if it's there, then making it! that's nuts!
        hfi = await get_hfi(session, for_date)
        if hfi.first() is None:
            await process_hfi(for_date)

        rows = await get_hfi_area_percentages(session, for_date)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area

            zones.append(FireZoneArea(
                mof_fire_zone_id=row.source_identifier,
                elevated_hfi_area=row.hfi_area,
                elevated_hfi_percentage=hfi_area / zone_area * 100))
        return FireZoneAreaListResponse(zones=zones)
