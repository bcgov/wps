""" Routers for new/formal/non-tinker fba.
"""
import logging
from datetime import date
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from advisory.db.database.tileserver import get_tileserver_read_session_scope
from advisory.db.crud import get_simple_hfi_area_percentages
from app.auth import authentication_required, audit
from app.schemas.fba import FireCenterListResponse, FireZoneAreaListResponse, FireZoneArea
from app.wildfire_one.wfwx_api import (get_auth_header, get_fire_centers)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get('/fire-centers', response_model=FireCenterListResponse)
async def get_all_fire_centers(_=Depends(authentication_required)):
    """ Returns fire centers for all active stations. """
    logger.info('/fba/fire-centers/')
    async with ClientSession() as session:
        header = await get_auth_header(session)
        fire_centers = await get_fire_centers(session, header)
    return FireCenterListResponse(fire_centers=fire_centers)


@router.get('/fire-zone-areas/{for_date}', response_model=FireZoneAreaListResponse)
async def get_zones(for_date: date, _=Depends(authentication_required)):
    async with get_tileserver_read_session_scope() as session:
        zones = []
        rows = await get_simple_hfi_area_percentages(session, for_date)

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
