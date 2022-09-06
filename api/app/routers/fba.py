""" Routers for new/formal/non-tinker fba.
"""
import os
import logging
from datetime import date
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
import tempfile
from shapely.geometry import Polygon
from shapely import wkb
from app import config
from advisory.db.database.tileserver import get_tileserver_read_session_scope
from advisory.db.crud import get_hfi_area_percentages
from app.db.database import get_async_write_session_scope
from app.db.crud.fba_advisory import save_hfi
from app.db.models.advisory import ClassifiedHfi
from app.auth import authentication_required
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
            geojson = polygonize(temp_filename)
            for feature in geojson.get('features', {}):
                properties = feature.get('properties', {})
                hfi = properties.get('hfi', None)
                if hfi == 1:
                    hfi = '4000 > hfi < 10000'
                elif hfi == 2:
                    hfi = 'hfi >= 10000'
                geometry = feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                if hfi is not None and coordinates is not None:
                    geom = Polygon(coordinates[0])
                    wkt = wkb.dumps(geom, hex=True, srid=3005)
                    obj = ClassifiedHfi(hfi=hfi, date=for_date, geom=wkt)
                    await save_hfi(session, obj)


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
    async with get_tileserver_read_session_scope() as session:
        zones = []

        # this is a slow step! checking to see if it's there, then making it! that's nuts!
        # hfi = await get_hfi(session, for_date)
        # if hfi.first() is None:
        #     await process_hfi(for_date)

        rows = await get_hfi_area_percentages(session, for_date)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area
            print(f'{row.mof_fire_zone_name}:{hfi_area}/{zone_area}={hfi_area/zone_area*100}%')

            zones.append(FireZoneArea(
                mof_fire_zone_id=row.mof_fire_zone_id,
                elevated_hfi_area=row.hfi_area,
                elevated_hfi_percentage=hfi_area / zone_area * 100))
        return FireZoneAreaListResponse(zones=zones)
