"""Routers for Auto Spatial Advisory"""

import logging
import math
from collections import defaultdict
from datetime import date, datetime
from typing import List

from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends

from app.auto_spatial_advisory.fuel_type_layer import (
    get_fuel_type_raster_by_year,
)
from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.zone_stats import (
    get_fuel_type_area_stats,
    get_zone_wind_stats_for_source_id,
)
from wps_shared.auth import asa_authentication_required, audit, audit_asa
from wps_shared.db.crud.auto_spatial_advisory import (
    get_all_hfi_thresholds_by_id,
    get_all_sfms_fuel_type_records,
    get_all_zone_source_ids,
    get_centre_tpi_stats,
    get_fire_centre_tpi_fuel_areas,
    get_hfi_area,
    get_min_wind_speed_hfi_thresholds,
    get_most_recent_run_datetime_for_date,
    get_most_recent_run_datetime_for_date_range,
    get_precomputed_stats_for_shape,
    get_provincial_rollup,
    get_run_datetimes,
    get_sfms_bounds,
    get_tpi_fuel_areas,
    get_tpi_stats,
    get_zone_source_ids_in_centre,
)
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum, TPIClassEnum
from wps_shared.schemas.fba import (
    FireCenterListResponse,
    FireCentreTPIResponse,
    FireShapeArea,
    FireShapeAreaDetail,
    FireShapeAreaListResponse,
    FireZoneHFIStats,
    FireZoneTPIStats,
    HFIStatsResponse,
    LatestSFMSRunParameter,
    LatestSFMSRunParameterRangeResponse,
    LatestSFMSRunParameterResponse,
    ProvincialSummaryResponse,
    SFMSBoundsResponse,
    SFMSRunParameter,
    TPIResponse,
)
from wps_shared.wildfire_one.wfwx_api import get_auth_header, get_fire_centers

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fba",
    dependencies=[Depends(asa_authentication_required), Depends(audit_asa)],
)


@router.get("/fire-centers", response_model=FireCenterListResponse)
async def get_all_fire_centers(_=Depends(asa_authentication_required)):
    """Returns fire centers for all active stations."""
    logger.info("/fba/fire-centers/")
    async with ClientSession() as session:
        header = await get_auth_header(session)
        fire_centers = await get_fire_centers(session, header)
    return FireCenterListResponse(fire_centers=fire_centers)


@router.get(
    "/fire-shape-areas/{run_type}/{run_datetime}/{for_date}",
    response_model=FireShapeAreaListResponse,
)
async def get_shapes(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """Return area of each zone unit shape, and percentage of area of zone unit shape with high hfi."""
    async with get_async_read_session_scope() as session:
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        shapes = []

        rows = await get_hfi_area(
            session, RunTypeEnum(run_type.value), run_datetime, for_date, fuel_type_raster.id
        )

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


@router.get(
    "/provincial-summary/{run_type}/{run_datetime}/{for_date}",
    response_model=ProvincialSummaryResponse,
)
async def get_provincial_summary(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """Return all Fire Centres with their fire shapes and the HFI status of those shapes."""
    logger.info("/fba/provincial_summary/")
    async with get_async_read_session_scope() as session:
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        fire_shape_area_details = []
        rows = await get_provincial_rollup(
            session, RunTypeEnum(run_type.value), run_datetime, for_date, fuel_type_raster.id
        )
        for row in rows:
            elevated_hfi_percentage = 0
            if row.hfi_area is not None and row.combustible_area is not None:
                elevated_hfi_percentage = row.hfi_area / row.combustible_area * 100
            fire_shape_area_details.append(
                FireShapeAreaDetail(
                    fire_shape_id=row.source_identifier,
                    fire_shape_name=row.placename_label,
                    fire_centre_name=row.fire_centre_name,
                    threshold=row.threshold,
                    combustible_area=row.combustible_area,
                    elevated_hfi_area=row.hfi_area,
                    elevated_hfi_percentage=elevated_hfi_percentage,
                )
            )
    return ProvincialSummaryResponse(provincial_summary=fire_shape_area_details)


@router.get(
    "/fire-centre-hfi-stats/{run_type}/{for_date}/{run_datetime}/{fire_centre_name}",
    response_model=dict[str, dict[int, FireZoneHFIStats]],
)
async def get_hfi_fuels_data_for_fire_centre(
    run_type: RunType,
    for_date: date,
    run_datetime: datetime,
    fire_centre_name: str,
    _=Depends(asa_authentication_required),
):
    """
    Fetch fuel type and critical hours data for all fire zones in a fire centre for a given date
    """
    logger.info(
        "fire-centre-hfi-stats/%s/%s/%s/%s",
        run_type.value,
        for_date,
        run_datetime,
        fire_centre_name,
    )

    async with get_async_read_session_scope() as session:
        # get fuel type ids data
        fuel_types = await get_all_sfms_fuel_type_records(session)
        # get fire zone id's within a fire centre
        zone_source_ids = await get_zone_source_ids_in_centre(session, fire_centre_name)
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        zone_wind_stats_by_source_id = {}
        hfi_thresholds_by_id = await get_all_hfi_thresholds_by_id(session)
        advisory_wind_speed_by_source_id = await get_min_wind_speed_hfi_thresholds(
            session, zone_source_ids, run_type, run_datetime, for_date
        )
        for source_id, wind_speed_stats in advisory_wind_speed_by_source_id.items():
            min_wind_stats = get_zone_wind_stats_for_source_id(
                wind_speed_stats, hfi_thresholds_by_id
            )
            zone_wind_stats_by_source_id[source_id] = min_wind_stats

        all_zone_data: dict[int, FireZoneHFIStats] = {}
        for zone_source_id in zone_source_ids:
            # get HFI/fuels data for specific zone
            hfi_fuel_type_ids_for_zone = await get_precomputed_stats_for_shape(
                session,
                run_type=RunTypeEnum(run_type.value),
                for_date=for_date,
                run_datetime=run_datetime,
                source_identifier=zone_source_id,
                fuel_type_raster_id=fuel_type_raster.id,
            )

            if hfi_fuel_type_ids_for_zone is None or len(hfi_fuel_type_ids_for_zone) == 0:
                # Handle the situation where data for the current year was actually processed with
                # last year's fuel grid
                prev_fuel_type_raster = await get_fuel_type_raster_by_year(
                    session, for_date.year - 1
                )
                hfi_fuel_type_ids_for_zone = await get_precomputed_stats_for_shape(
                    session,
                    run_type=RunTypeEnum(run_type.value),
                    for_date=for_date,
                    run_datetime=run_datetime,
                    source_identifier=zone_source_id,
                    fuel_type_raster_id=prev_fuel_type_raster.id,
                )

            zone_fuel_stats = []

            for (
                critical_hour_start,
                critical_hour_end,
                fuel_type_id,
                threshold_id,
                area,
                fuel_area,
                percent_conifer,
            ) in hfi_fuel_type_ids_for_zone:
                hfi_threshold = hfi_thresholds_by_id.get(threshold_id)
                if hfi_threshold is None:
                    logger.error(f"No hfi threshold for id: {threshold_id}")
                    continue
                fuel_type_area_stats = get_fuel_type_area_stats(
                    for_date,
                    fuel_types,
                    hfi_threshold,
                    percent_conifer,
                    critical_hour_start,
                    critical_hour_end,
                    fuel_type_id,
                    area,
                    fuel_area,
                )
                zone_fuel_stats.append(fuel_type_area_stats)

            all_zone_data[int(zone_source_id)] = FireZoneHFIStats(
                min_wind_stats=zone_wind_stats_by_source_id.get(int(zone_source_id), []),
                fuel_area_stats=zone_fuel_stats,
            )

        return {fire_centre_name: all_zone_data}


@router.get("/latest-sfms-run-datetime/{for_date}", response_model=LatestSFMSRunParameterResponse)
async def get_latest_sfms_run_datetime_for_date(
    for_date: date,
    _=Depends(asa_authentication_required),
):
    async with get_async_read_session_scope() as session:
        latest_run_parameter = await get_most_recent_run_datetime_for_date(session, for_date)
        if latest_run_parameter is None:
            return LatestSFMSRunParameterResponse()
        run_parameter = LatestSFMSRunParameter(
            for_date=latest_run_parameter.for_date,
            run_datetime=latest_run_parameter.run_datetime,
            run_type=latest_run_parameter.run_type,
        )
        return LatestSFMSRunParameterResponse(run_parameter=run_parameter)


@router.get("/sfms-run-bounds", response_model=SFMSBoundsResponse)
async def get_sfms_run_bounds():
    async with get_async_read_session_scope() as session:
        results = await get_sfms_bounds(session)
        sfms_bounds = defaultdict(lambda: defaultdict(lambda: defaultdict(date)))
        for year, run_type, min_date, max_date in results:
            sfms_bounds[year][run_type]["minimum"] = min_date
            sfms_bounds[year][run_type]["maximum"] = max_date
    return SFMSBoundsResponse(sfms_bounds=sfms_bounds)


@router.get(
    "/fire-centre-tpi-stats/{run_type}/{for_date}/{run_datetime}/{fire_centre_name}",
    response_model=FireCentreTPIResponse,
)
async def get_fire_centre_tpi_stats(
    fire_centre_name: str,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """Return the elevation TPI statistics for each advisory threshold for a fire centre"""
    logger.info("/fba/fire-centre-tpi-stats/")
    async with get_async_read_session_scope() as session:
        tpi_stats_for_centre = await get_centre_tpi_stats(
            session, fire_centre_name, run_type, run_datetime, for_date
        )
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        tpi_fuel_stats = await get_fire_centre_tpi_fuel_areas(
            session, fire_centre_name, fuel_type_raster.id
        )
        hfi_tpi_areas_by_zone = []
        for row in tpi_stats_for_centre:
            fire_zone_id = row.source_identifier
            square_metres = math.pow(row.pixel_size_metres, 2)
            tpi_fuel_stats_for_zone = [
                stats for stats in tpi_fuel_stats if stats[2] == fire_zone_id
            ]
            valley_bottom_tpi = None
            mid_slope_tpi = None
            upper_slope_tpi = None

            for tpi_fuel_stat in tpi_fuel_stats_for_zone:
                if tpi_fuel_stat[0] == TPIClassEnum.valley_bottom:
                    valley_bottom_tpi = tpi_fuel_stat[1]
                elif tpi_fuel_stat[0] == TPIClassEnum.mid_slope:
                    mid_slope_tpi = tpi_fuel_stat[1]
                elif tpi_fuel_stat[0] == TPIClassEnum.upper_slope:
                    upper_slope_tpi = tpi_fuel_stat[1]

            hfi_tpi_areas_by_zone.append(
                FireZoneTPIStats(
                    fire_zone_id=fire_zone_id,
                    valley_bottom_hfi=row.valley_bottom * square_metres,
                    valley_bottom_tpi=valley_bottom_tpi,
                    mid_slope_hfi=row.mid_slope * square_metres,
                    mid_slope_tpi=mid_slope_tpi,
                    upper_slope_hfi=row.upper_slope * square_metres,
                    upper_slope_tpi=upper_slope_tpi,
                )
            )

    return FireCentreTPIResponse(
        fire_centre_name=fire_centre_name, firezone_tpi_stats=hfi_tpi_areas_by_zone
    )


@router.get(
    "/latest-sfms-run-parameters/{start_date}/{end_date}",
    response_model=LatestSFMSRunParameterRangeResponse,
)
async def get_latest_sfms_run_datetime_for_date_range(
    start_date: date,
    end_date: date,
    _=Depends(asa_authentication_required),
):
    async with get_async_read_session_scope() as session:
        result = await get_most_recent_run_datetime_for_date_range(session, start_date, end_date)
        latest_run_parameters = {}
        for row in result:
            run_parameter = SFMSRunParameter(
                for_date=row.for_date, run_type=row.run_type, run_datetime=row.run_datetime
            )
            latest_run_parameters[row.for_date] = run_parameter
        return LatestSFMSRunParameterRangeResponse(run_parameters=latest_run_parameters)


#### ASA Go Specific Routes ####


@router.get("/sfms-run-datetimes/{run_type}/{for_date}", response_model=List[datetime])
async def get_run_datetimes_for_date_and_runtype(
    run_type: RunType,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """Return list of datetimes for which SFMS has run, given a specific for_date and run_type.
    Datetimes should be ordered with most recent first."""
    async with get_async_read_session_scope() as session:
        datetimes = []

        rows = await get_run_datetimes(session, RunTypeEnum(run_type.value), for_date)

        for row in rows:
            datetimes.append(row.run_datetime)  # type: ignore

        return datetimes


@router.get(
    "/hfi-stats/{run_type}/{run_datetime}/{for_date}",
    response_model=HFIStatsResponse,
)
async def get_hfi_fuels_data_for_run_parameter(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """
    Fetch fuel type and critical hours data for all fire zones units
    """
    logger.info(
        "hfi-stats/%s/%s/%s",
        run_type.value,
        for_date,
        run_datetime,
    )

    async with get_async_read_session_scope() as session:
        # get fuel type ids data
        fuel_types = await get_all_sfms_fuel_type_records(session)
        # get fire zone id's within a fire centre
        zone_source_ids = await get_all_zone_source_ids(session)
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        zone_wind_stats_by_source_id = {}
        hfi_thresholds_by_id = await get_all_hfi_thresholds_by_id(session)
        advisory_wind_speed_by_source_id = await get_min_wind_speed_hfi_thresholds(
            session, zone_source_ids, run_type, run_datetime, for_date
        )
        for source_id, wind_speed_stats in advisory_wind_speed_by_source_id.items():
            min_wind_stats = get_zone_wind_stats_for_source_id(
                wind_speed_stats, hfi_thresholds_by_id
            )
            zone_wind_stats_by_source_id[source_id] = min_wind_stats

        all_zone_data: dict[int, FireZoneHFIStats] = {}
        for zone_source_id in zone_source_ids:
            # get HFI/fuels data for specific zone
            hfi_fuel_type_ids_for_zone = await get_precomputed_stats_for_shape(
                session,
                run_type=RunTypeEnum(run_type.value),
                for_date=for_date,
                run_datetime=run_datetime,
                source_identifier=zone_source_id,
                fuel_type_raster_id=fuel_type_raster.id,
            )

            if hfi_fuel_type_ids_for_zone is None or len(hfi_fuel_type_ids_for_zone) == 0:
                # Handle the situation where data for the current year was actually processed with
                # last year's fuel grid
                prev_fuel_type_raster = await get_fuel_type_raster_by_year(
                    session, for_date.year - 1
                )
                hfi_fuel_type_ids_for_zone = await get_precomputed_stats_for_shape(
                    session,
                    run_type=RunTypeEnum(run_type.value),
                    for_date=for_date,
                    run_datetime=run_datetime,
                    source_identifier=zone_source_id,
                    fuel_type_raster_id=prev_fuel_type_raster.id,
                )

            zone_fuel_stats = []

            for (
                critical_hour_start,
                critical_hour_end,
                fuel_type_id,
                threshold_id,
                area,
                fuel_area,
                percent_conifer,
            ) in hfi_fuel_type_ids_for_zone:
                hfi_threshold = hfi_thresholds_by_id.get(threshold_id)
                if hfi_threshold is None:
                    logger.error(f"No hfi threshold for id: {threshold_id}")
                    continue
                fuel_type_area_stats = get_fuel_type_area_stats(
                    for_date,
                    fuel_types,
                    hfi_threshold,
                    percent_conifer,
                    critical_hour_start,
                    critical_hour_end,
                    fuel_type_id,
                    area,
                    fuel_area,
                )
                zone_fuel_stats.append(fuel_type_area_stats)

            all_zone_data[int(zone_source_id)] = FireZoneHFIStats(
                min_wind_stats=zone_wind_stats_by_source_id.get(int(zone_source_id), []),
                fuel_area_stats=zone_fuel_stats,
            )

        return HFIStatsResponse(zone_data=all_zone_data)


@router.get(
    "/tpi-stats/{run_type}/{run_datetime}/{for_date}",
    response_model=TPIResponse,
)
async def get_tpi_stats_for_run_parameter(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    _=Depends(asa_authentication_required),
):
    """Return the elevation TPI statistics for each advisory threshold for all fire shapes"""
    logger.info("/fba/tpi-stats/")
    async with get_async_read_session_scope() as session:
        tpi_stats = await get_tpi_stats(session, run_type, run_datetime, for_date)
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        tpi_fuel_stats = await get_tpi_fuel_areas(session, fuel_type_raster.id)
        hfi_tpi_areas_by_zone = []
        for row in tpi_stats:
            fire_zone_id = row.source_identifier
            square_metres = math.pow(row.pixel_size_metres, 2)
            tpi_fuel_stats_for_zone = [
                stats for stats in tpi_fuel_stats if stats[2] == fire_zone_id
            ]
            valley_bottom_tpi = None
            mid_slope_tpi = None
            upper_slope_tpi = None

            for tpi_fuel_stat in tpi_fuel_stats_for_zone:
                if tpi_fuel_stat[0] == TPIClassEnum.valley_bottom:
                    valley_bottom_tpi = tpi_fuel_stat[1]
                elif tpi_fuel_stat[0] == TPIClassEnum.mid_slope:
                    mid_slope_tpi = tpi_fuel_stat[1]
                elif tpi_fuel_stat[0] == TPIClassEnum.upper_slope:
                    upper_slope_tpi = tpi_fuel_stat[1]

            hfi_tpi_areas_by_zone.append(
                FireZoneTPIStats(
                    fire_zone_id=fire_zone_id,
                    valley_bottom_hfi=row.valley_bottom * square_metres,
                    valley_bottom_tpi=valley_bottom_tpi,
                    mid_slope_hfi=row.mid_slope * square_metres,
                    mid_slope_tpi=mid_slope_tpi,
                    upper_slope_hfi=row.upper_slope * square_metres,
                    upper_slope_tpi=upper_slope_tpi,
                )
            )

    return TPIResponse(firezone_tpi_stats=hfi_tpi_areas_by_zone)
