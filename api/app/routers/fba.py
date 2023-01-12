""" Routers for Auto Spatial Advisory
"""

import logging
from datetime import date, datetime
from typing import List
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.db.database import get_async_read_session_scope
from app.db.crud.auto_spatial_advisory import get_hfi_area, get_run_datetimes
from app.auth import authentication_required, audit
from app.db.models.auto_spatial_advisory import RunTypeEnum
from app.schemas.fba import FireCenterListResponse, FireZoneAreaListResponse, FireZoneArea,\
    FireZoneHighHfiAreas, FireZoneHighHfiAreasListResponse
from app.wildfire_one.wfwx_api import (get_auth_header, get_fire_centers)
from app.auto_spatial_advisory.process_hfi import RunType

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
async def get_zones(run_type: RunType, run_datetime: datetime, for_date: date, _=Depends(authentication_required)):
    """ Return area of each zone, and percentage of area of zone with high hfi. """
    async with get_async_read_session_scope() as session:
        zones = []

        rows = await get_hfi_area(session,
                                  RunTypeEnum(run_type.value),
                                  run_datetime,
                                  for_date)

        # Fetch rows.
        for row in rows:
            combustible_area = row.combustible_area  # type: ignore
            hfi_area = row.hfi_area  # type: ignore
            zones.append(FireZoneArea(
                mof_fire_zone_id=row.source_identifier,  # type: ignore
                elevated_hfi_area=row.hfi_area,  # type: ignore
                elevated_hfi_percentage=hfi_area / combustible_area * 100))
        return FireZoneAreaListResponse(zones=zones)


@router.get('/sfms_run_datetimes/{run_type}/{for_date}', response_model=List[datetime])
async def get_run_datetimes_for_date_and_runtype(run_type: RunType, for_date: date, _=Depends(authentication_required)):
    """ Return list of datetimes for which SFMS has run, given a specific for_date and run_type.
    Datetimes should be ordered with most recent first. """
    async with get_async_read_session_scope() as session:
        datetimes = []

        rows = await get_run_datetimes(session, RunTypeEnum(run_type.value), for_date)

        for row in rows:
            datetimes.append(row.run_datetime)  # type: ignore

        return datetimes


@router.get('/fire-zone-hfi-areas/{run_type}/{run_date}/{for_date}',
            response_model=FireZoneHighHfiAreasListResponse)
async def get_high_hfi_areas_per_zone(run_type: RunType,
                                      run_date: date,
                                      for_date: date,
                                      _=Depends(authentication_required)):
    """ Return the areas exceeding high HFI thresholds for each fire zone """
    async with get_async_read_session_scope() as session:
        zones = []

        rows = await get_high_hfi_areas_per_zone(session,
                                                 RunTypeEnum(run_type.value),
                                                 run_date,
                                                 for_date)

        for row in rows:
            zones.append(FireZoneHighHfiAreas(
                mof_fire_zone_id=row.source_identifier,
                advisory_area=row.advisory_area,
                warn_area=row.warn_area))
        return FireZoneHighHfiAreasListResponse(zones=zones)
