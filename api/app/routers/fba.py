""" Routers for Auto Spatial Advisory
"""

from itertools import groupby
import logging
from datetime import date, datetime
import operator
from typing import List
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.db.database import get_async_read_session_scope
from app.db.crud.auto_spatial_advisory import (get_fuel_types_with_high_hfi, get_hfi_area, get_run_datetimes,
                                               get_zonal_elevation_stats)
from app.auth import authentication_required, audit
from app.db.models.auto_spatial_advisory import RunTypeEnum
from app.schemas.fba import FireCenterListResponse, FireZoneAreaListResponse, FireZoneArea, HfiThresholdAreaByFuelType,\
    FireZoneElevationStats, FireZoneElevationStatsByThreshold, FireZoneElevationStatsListResponse
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


@router.get('/fire-zone-areas/{run_type}/{run_datetime}/{for_date}',
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
                threshold=row.threshold,  # type: ignore
                combustible_area=row.combustible_area,  # type: ignore
                elevated_hfi_area=row.hfi_area,  # type: ignore
                elevated_hfi_percentage=hfi_area / combustible_area * 100))
        return FireZoneAreaListResponse(zones=zones)


@router.get('/hfi-fuels/{run_type}/{for_date}/{run_datetime}',
            response_model=dict[str, List[HfiThresholdAreaByFuelType]])
async def get_hfi_thresholds_by_fuel_type(run_type: RunType,
                                          for_date: date,
                                          run_datetime: datetime):
    """
    Get the fuel types for the run_type, for_date, run_date
    """
    logger.info('hfi-fuels/%s/%s/%s', run_type.value, for_date, run_datetime)
    async with get_async_read_session_scope() as session:
        fuel_types_high_hfi = await get_fuel_types_with_high_hfi(
            session,
            run_type=RunTypeEnum(run_type.value),
            for_date=for_date,
            run_datetime=run_datetime
        )

        fuel_stats_by_fire_zone = groupby(fuel_types_high_hfi, operator.itemgetter(0))
        fire_zone_stats = dict((k, list(map(lambda x: x, values))) for k, values in fuel_stats_by_fire_zone)

        for zone_id, tuples_list in fire_zone_stats.items():
            hfi_areas_for_zone = []
            for record in tuples_list:
                hfi_areas_for_zone.append(HfiThresholdAreaByFuelType(fuel_type_id=record[1],
                                                                     threshold=record[2], area=record[3]))
            fire_zone_stats[zone_id] = hfi_areas_for_zone

        return fire_zone_stats


@router.get('/sfms-run-datetimes/{run_type}/{for_date}', response_model=List[datetime])
async def get_run_datetimes_for_date_and_runtype(run_type: RunType, for_date: date, _=Depends(authentication_required)):
    """ Return list of datetimes for which SFMS has run, given a specific for_date and run_type.
    Datetimes should be ordered with most recent first. """
    async with get_async_read_session_scope() as session:
        datetimes = []

        rows = await get_run_datetimes(session, RunTypeEnum(run_type.value), for_date)

        for row in rows:
            datetimes.append(row.run_datetime)  # type: ignore

        return datetimes


@router.get('/fire-zone-elevation-stats/{fire_zone_id}/{run_type}/{run_datetime}/{for_date}',
            response_model=FireZoneElevationStatsListResponse)
async def get_fire_zone_elevation_stats(fire_zone_id: int, run_type: RunType, run_datetime: datetime, for_date: date,
                                        _=Depends(authentication_required)):
    """ Return the elevation statistics for each advisory threshold """
    async with get_async_read_session_scope() as session:
        data = []
        rows = get_zonal_elevation_stats(session, fire_zone_id, RunTypeEnum(run_type.value), run_datetime, for_date)
        for row in rows:
            stats = FireZoneElevationStats(
                minimum=row.minimum,
                quartile_25=row.quartile_25,
                median=row.median,
                quartile_75=row.quartile_75,
                maximum=row.maximum)
            stats_by_threshold = FireZoneElevationStatsByThreshold(threshold=row.threshold, stats=stats)
            data.append(stats_by_threshold)
        return FireZoneElevationStatsListResponse(data=data)
