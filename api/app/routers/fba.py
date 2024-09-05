"""Routers for Auto Spatial Advisory"""

import logging
import math
from datetime import date, datetime
from typing import List
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.db.database import get_async_read_session_scope
from app.db.crud.auto_spatial_advisory import (
    get_all_sfms_fuel_types,
    get_all_hfi_thresholds,
    get_hfi_area,
    get_precomputed_high_hfi_fuel_type_areas_for_shape,
    get_provincial_rollup,
    get_run_datetimes,
    get_zonal_elevation_stats,
    get_zonal_tpi_stats,
)
from app.db.models.auto_spatial_advisory import RunTypeEnum
from app.schemas.fba import (
    ClassifiedHfiThresholdFuelTypeArea,
    FireCenterListResponse,
    FireShapeAreaListResponse,
    FireShapeArea,
    FireZoneElevationStats,
    FireZoneElevationStatsByThreshold,
    FireZoneElevationStatsListResponse,
    FireZoneTPIStats,
    SFMSFuelType,
    HfiThreshold,
    FireShapeAreaDetail,
    ProvincialSummaryResponse,
)
from app.auth import authentication_required, audit
from app.wildfire_one.wfwx_api import get_auth_header, get_fire_centers
from app.auto_spatial_advisory.process_hfi import RunType

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


@router.get("/fire-centers", response_model=FireCenterListResponse)
async def get_all_fire_centers(_=Depends(authentication_required)):
    """Returns fire centers for all active stations."""
    logger.info("/fba/fire-centers/")
    async with ClientSession() as session:
        header = await get_auth_header(session)
        fire_centers = await get_fire_centers(session, header)
    return FireCenterListResponse(fire_centers=fire_centers)


@router.get("/fire-shape-areas/{run_type}/{run_datetime}/{for_date}", response_model=FireShapeAreaListResponse)
async def get_shapes(run_type: RunType, run_datetime: datetime, for_date: date, _=Depends(authentication_required)):
    """Return area of each zone unit shape, and percentage of area of zone unit shape with high hfi."""
    async with get_async_read_session_scope() as session:
        shapes = []

        rows = await get_hfi_area(session, RunTypeEnum(run_type.value), run_datetime, for_date)

        # Fetch rows.
        for row in rows:
            combustible_area = row.combustible_area  # type: ignore
            hfi_area = row.hfi_area  # type: ignore
            shapes.append(
                FireShapeArea(
                    fire_shape_id=row.source_identifier,  # type: ignore
                    threshold=row.threshold,  # type: ignore
                    combustible_area=row.combustible_area,  # type: ignore
                    elevated_hfi_area=row.hfi_area,  # type: ignore
                    elevated_hfi_percentage=hfi_area / combustible_area * 100,
                )
            )
        return FireShapeAreaListResponse(shapes=shapes)


@router.get("/provincial-summary/{run_type}/{run_datetime}/{for_date}", response_model=ProvincialSummaryResponse)
async def get_provincial_summary(run_type: RunType, run_datetime: datetime, for_date: date, _=Depends(authentication_required)):
    """Return all Fire Centres with their fire shapes and the HFI status of those shapes."""
    logger.info("/fba/provincial_summary/")
    async with get_async_read_session_scope() as session:
        fire_shape_area_details = []
        rows = await get_provincial_rollup(session, RunTypeEnum(run_type.value), run_datetime, for_date)
        for row in rows:
            elevated_hfi_percentage = 0
            if row.hfi_area is not None and row.combustible_area is not None:
                elevated_hfi_percentage = row.hfi_area / row.combustible_area * 100
            fire_shape_area_details.append(
                FireShapeAreaDetail(
                    fire_shape_id=row.source_identifier,
                    fire_shape_name=row.label,
                    fire_centre_name=row.fire_centre_name,
                    threshold=row.threshold,
                    combustible_area=row.combustible_area,
                    elevated_hfi_area=row.hfi_area,
                    elevated_hfi_percentage=elevated_hfi_percentage,
                )
            )
    return ProvincialSummaryResponse(provincial_summary=fire_shape_area_details)


@router.get("/hfi-fuels/{run_type}/{for_date}/{run_datetime}/{zone_id}", response_model=dict[int, List[ClassifiedHfiThresholdFuelTypeArea]])
async def get_hfi_fuels_data_for_fire_zone(run_type: RunType, for_date: date, run_datetime: datetime, zone_id: int):
    """
    Fetch rollup of fuel type/HFI threshold/area data for a specified fire zone.
    """
    logger.info("hfi-fuels/%s/%s/%s/%s", run_type.value, for_date, run_datetime, zone_id)

    async with get_async_read_session_scope() as session:
        # get thresholds data
        thresholds = await get_all_hfi_thresholds(session)
        # get fuel type ids data
        fuel_types = await get_all_sfms_fuel_types(session)

        # get HFI/fuels data for specific zone
        hfi_fuel_type_ids_for_zone = await get_precomputed_high_hfi_fuel_type_areas_for_shape(
            session, run_type=RunTypeEnum(run_type.value), for_date=for_date, run_datetime=run_datetime, advisory_shape_id=zone_id
        )
        data = []

        for record in hfi_fuel_type_ids_for_zone:
            fuel_type_id = record[1]
            threshold_id = record[2]
            # area is stored in square metres in DB. For user convenience, convert to hectares
            # 1 ha = 10,000 sq.m.
            area = record[3] / 10000
            fuel_type_obj = next((ft for ft in fuel_types if ft.fuel_type_id == fuel_type_id), None)
            threshold_obj = next((th for th in thresholds if th.id == threshold_id), None)
            data.append(
                ClassifiedHfiThresholdFuelTypeArea(
                    fuel_type=SFMSFuelType(fuel_type_id=fuel_type_obj.fuel_type_id, fuel_type_code=fuel_type_obj.fuel_type_code, description=fuel_type_obj.description),
                    threshold=HfiThreshold(id=threshold_obj.id, name=threshold_obj.name, description=threshold_obj.description),
                    area=area,
                )
            )

        return {zone_id: data}


@router.get("/sfms-run-datetimes/{run_type}/{for_date}", response_model=List[datetime])
async def get_run_datetimes_for_date_and_runtype(run_type: RunType, for_date: date, _=Depends(authentication_required)):
    """Return list of datetimes for which SFMS has run, given a specific for_date and run_type.
    Datetimes should be ordered with most recent first."""
    async with get_async_read_session_scope() as session:
        datetimes = []

        rows = await get_run_datetimes(session, RunTypeEnum(run_type.value), for_date)

        for row in rows:
            datetimes.append(row.run_datetime)  # type: ignore

        return datetimes


@router.get("/fire-zone-tpi-stats/{run_type}/{for_date}/{run_datetime}/{fire_zone_id}", response_model=FireZoneTPIStats)
async def get_fire_zone_tpi_stats(fire_zone_id: int, run_type: RunType, run_datetime: datetime, for_date: date, _=Depends(authentication_required)):
    """Return the elevation TPI statistics for each advisory threshold"""
    logger.info("/fba/fire-zone-tpi-stats/")
    async with get_async_read_session_scope() as session:
        stats = await get_zonal_tpi_stats(session, fire_zone_id, run_type, run_datetime, for_date)
        square_metres = math.pow(stats.pixel_size_metres, 2)
        return FireZoneTPIStats(
            fire_zone_id=fire_zone_id,
            valley_bottom=stats.valley_bottom * square_metres,
            mid_slope=stats.mid_slope * square_metres,
            upper_slope=stats.upper_slope * square_metres,
        )
