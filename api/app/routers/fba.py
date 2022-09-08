""" Routers for Auto Spatial Advisory
"""

import logging
from datetime import date
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.db.database import get_async_read_session_scope
from app.db.crud.fba_advisory import get_hfi_area, get_hfi
from app.auth import authentication_required, audit
from app.db.models.advisory import RunTypeEnum
from app.schemas.fba import FireCenterListResponse, FireZoneAreaListResponse, FireZoneArea
from app.wildfire_one.wfwx_api import (get_auth_header, get_fire_centers)
from app.auto_spatial_advisory.process_hfi import process_hfi, RunType

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


@router.get('/fire-zone-areas/{run_type}/{run_date}/{for_date}',
            response_model=FireZoneAreaListResponse)
async def get_zones(run_type: RunType, run_date: date, for_date: date, _=Depends(authentication_required)):
    """ Return area of each zone, and percentage of area of zone with high hfi. """
    async with get_async_read_session_scope() as session:
        zones = []

        # this is a slow step! checking to see if it's there, then making it! this is just a
        # temporary workaround until we have automation in place.
        hfi = await get_hfi(session, RunTypeEnum(run_type.value), run_date, for_date)
        if hfi.first() is None:
            await process_hfi(run_type, run_date, for_date)

        rows = await get_hfi_area(session,
                                  RunTypeEnum(run_type.value),
                                  run_date,
                                  for_date)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area

            zones.append(FireZoneArea(
                mof_fire_zone_id=row.source_identifier,
                elevated_hfi_area=row.hfi_area,
                elevated_hfi_percentage=hfi_area / zone_area * 100))
        return FireZoneAreaListResponse(zones=zones)
