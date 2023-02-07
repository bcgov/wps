""" Routers for Auto Spatial Advisory
"""

import logging
from datetime import date, datetime
from typing import List
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.db.database import get_async_read_session_scope
from app.db.crud.auto_spatial_advisory import (get_all_sfms_fuel_types,
                                               get_all_hfi_thresholds,
                                               get_hfi_area,
                                               get_high_hfi_fuel_types_for_zone,
                                               get_run_datetimes,
                                               get_zonal_elevation_stats)
from app.db.models.auto_spatial_advisory import RunTypeEnum
from app.schemas.fba import (ClassifiedHfiThresholdFuelTypeArea, FireCenterListResponse, FireZoneAreaListResponse,
                             FireZoneArea, FireZoneElevationStats, FireZoneElevationStatsByThreshold,
                             FireZoneElevationStatsListResponse, SFMSFuelType, HfiThreshold)
from app.auth import authentication_required, audit
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
                elevated_hfi_area=row.hfi_area,  # type: ignore
                elevated_hfi_percentage=hfi_area / combustible_area * 100))
        return FireZoneAreaListResponse(zones=zones)


@router.get('/hfi-fuels/{run_type}/{for_date}/{run_datetime}/{zone_id}',
            response_model=dict[int, List[ClassifiedHfiThresholdFuelTypeArea]])
async def get_hfi_fuels_data_for_fire_zone(run_type: RunType,
                                           for_date: date,
                                           run_datetime: datetime,
                                           zone_id: int):
    """
    Fetch rollup of fuel type/HFI threshold/area data for a specified fire zone.
    """
    logger.info('hfi-fuels/%s/%s/%s/%s', run_type.value, for_date, run_datetime, zone_id)

    async with get_async_read_session_scope() as session:
        # get thresholds data
        thresholds = await get_all_hfi_thresholds(session)
        # get fuel type ids data
        fuel_types = await get_all_sfms_fuel_types(session)

        # get HFI/fuels data for specific zone
        hfi_fuel_type_ids_for_zone = await get_high_hfi_fuel_types_for_zone(session,
                                                                            run_type=RunTypeEnum(run_type.value),
                                                                            for_date=for_date,
                                                                            run_datetime=run_datetime,
                                                                            zone_id=zone_id)
        data = []

        for record in hfi_fuel_type_ids_for_zone:
            fuel_type_id = record[1]
            threshold_id = record[2]
            # area is stored in square metres in DB. For user convenience, convert to hectares
            # 1 ha = 10,000 sq.m.
            area = record[3] / 10000
            fuel_type_obj = next((ft for ft in fuel_types if ft.fuel_type_id == fuel_type_id), None)
            threshold_obj = next((th for th in thresholds if th.id == threshold_id), None)
            data.append(ClassifiedHfiThresholdFuelTypeArea(
                fuel_type=SFMSFuelType(
                    fuel_type_id=fuel_type_obj.fuel_type_id,
                    fuel_type_code=fuel_type_obj.fuel_type_code,
                    description=fuel_type_obj.description
                ),
                threshold=HfiThreshold(
                    id=threshold_obj.id,
                    name=threshold_obj.name,
                    description=threshold_obj.description),
                area=area))

        return {zone_id: data}


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
