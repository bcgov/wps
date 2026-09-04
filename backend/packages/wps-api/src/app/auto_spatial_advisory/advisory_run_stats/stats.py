"""Advisory run stats: reads precomputed advisory data for a completed SFMS run (province-wide
fire shape status rollup, per-zone HFI stats, per-zone elevation TPI stats) and shapes it into
API responses, caching in Redis since this data never changes once a run completes."""

import asyncio
import logging
import math
from collections import defaultdict
from datetime import date, datetime
from typing import Awaitable, Callable, List, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.auto_spatial_advisory import (
    get_all_hfi_thresholds_by_id,
    get_all_sfms_fuel_type_records,
    get_all_zone_source_ids,
    get_centre_tpi_stats,
    get_fire_centre_tpi_fuel_areas,
    get_min_wind_speed_hfi_thresholds,
    get_precomputed_stats_for_shape,
    get_provincial_rollup,
    get_tpi_fuel_areas,
    get_zone_source_ids_in_centre,
)
from wps_shared.db.crud.auto_spatial_advisory import (
    get_tpi_stats as fetch_tpi_stats_rows,
)
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum, TPIClassEnum
from wps_shared.schemas.fba import (
    FireCentreTPIResponse,
    FireZoneHFIStats,
    FireZoneTPIStats,
    HFIStatsResponse,
    ProvincialSummaryResponse,
    TPIResponse,
)

from app.auto_spatial_advisory.advisory_run_stats.cache import asa_stats_cache
from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.zone_stats import (
    get_fuel_type_area_stats,
    get_zone_wind_stats_for_source_id,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# A completed run's data is the same for every caller (today/tomorrow), so a burst of
# concurrent requests all miss the cache at once and would otherwise all recompute in
# parallel instead of one caller computing it and the rest reading the cache. Keyed by the
# same (kind, run_type, run_datetime, for_date[, fire_centre_name]) tuple each call site
# already has this is unbounded but low-cardinality (one entry per run/day) and gunicorn recycles
# workers every ~50 requests anyway, so it never grows indefinitely.
_compute_locks: dict[tuple, asyncio.Lock] = defaultdict(asyncio.Lock)


async def _get_or_compute(
    key: tuple,
    get_cached: Callable[[], Awaitable[T | None]],
    compute: Callable[[], Awaitable[T]],
    put_cached: Callable[[T], Awaitable[None]],
) -> T:
    cached = await get_cached()
    if cached is not None:
        return cached
    async with _compute_locks[key]:
        # Re-check: another caller may have computed and cached this while we waited on the lock.
        cached = await get_cached()
        if cached is not None:
            return cached
        result = await compute()
        await put_cached(result)
        return result


async def get_all_zone_data_for_source_ids(
    session: AsyncSession,
    zone_source_ids: List[str],
    run_type: RunType,
    for_date: date,
    run_datetime: datetime,
):
    # get fuel type ids data
    fuel_types = await get_all_sfms_fuel_type_records(session)
    fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
    zone_wind_stats_by_source_id = {}
    hfi_thresholds_by_id = await get_all_hfi_thresholds_by_id(session)
    advisory_wind_speed_by_source_id = await get_min_wind_speed_hfi_thresholds(
        session, zone_source_ids, run_type, run_datetime, for_date
    )
    for source_id, wind_speed_stats in advisory_wind_speed_by_source_id.items():
        min_wind_stats = get_zone_wind_stats_for_source_id(wind_speed_stats, hfi_thresholds_by_id)
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
            prev_fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year - 1)
            hfi_fuel_type_ids_for_zone = await get_precomputed_stats_for_shape(
                session,
                run_type=RunTypeEnum(run_type.value),
                for_date=for_date,
                run_datetime=run_datetime,
                source_identifier=zone_source_id,
                fuel_type_raster_id=prev_fuel_type_raster.id,
            )

        zone_fuel_stats = []
        hfi_fuel_type_ids_for_zone_set = list(set(hfi_fuel_type_ids_for_zone))
        for (
            critical_hour_start,
            critical_hour_end,
            fuel_type_id,
            threshold_id,
            area,
            fuel_area,
            percent_conifer,
        ) in hfi_fuel_type_ids_for_zone_set:
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
    return all_zone_data


async def get_provincial_summary(
    run_type: RunType, run_datetime: datetime, for_date: date
) -> ProvincialSummaryResponse:
    """Return all Fire Centres with their fire shapes and the HFI status of those shapes."""

    async def compute() -> ProvincialSummaryResponse:
        async with get_async_read_session_scope() as session:
            fire_shape_status_details = await get_provincial_rollup(
                session, RunTypeEnum(run_type.value), run_datetime, for_date
            )
        return ProvincialSummaryResponse(provincial_summary=fire_shape_status_details)

    return await _get_or_compute(
        ("provincial_summary", run_type.value, run_datetime, for_date),
        lambda: asa_stats_cache.get_cached_provincial_summary(
            run_type.value, run_datetime, for_date
        ),
        compute,
        lambda response: asa_stats_cache.put_cached_provincial_summary(
            run_type.value, run_datetime, for_date, response
        ),
    )


async def get_hfi_stats(
    run_type: RunType, run_datetime: datetime, for_date: date
) -> HFIStatsResponse:
    """Fetch fuel type and critical hours data for all fire zone units."""

    async def compute() -> HFIStatsResponse:
        async with get_async_read_session_scope() as session:
            zone_source_ids = await get_all_zone_source_ids(session)
            all_zone_data = await get_all_zone_data_for_source_ids(
                session, zone_source_ids, run_type, for_date, run_datetime
            )
        return HFIStatsResponse(zone_data=all_zone_data)

    return await _get_or_compute(
        ("hfi_stats", run_type.value, run_datetime, for_date),
        lambda: asa_stats_cache.get_cached_hfi_stats(run_type.value, run_datetime, for_date),
        compute,
        lambda response: asa_stats_cache.put_cached_hfi_stats(
            run_type.value, run_datetime, for_date, response
        ),
    )


async def get_fire_centre_hfi_stats(
    fire_centre_name: str, run_type: RunType, run_datetime: datetime, for_date: date
) -> dict[int, FireZoneHFIStats]:
    """Fetch fuel type and critical hours data for all fire zones in one fire centre."""

    async def compute() -> dict[int, FireZoneHFIStats]:
        async with get_async_read_session_scope() as session:
            zone_source_ids = await get_zone_source_ids_in_centre(session, fire_centre_name)
            return await get_all_zone_data_for_source_ids(
                session, zone_source_ids, run_type, for_date, run_datetime
            )

    return await _get_or_compute(
        ("fire_centre_hfi_stats", fire_centre_name, run_type.value, run_datetime, for_date),
        lambda: asa_stats_cache.get_cached_fire_centre_hfi_stats(
            fire_centre_name, run_type.value, run_datetime, for_date
        ),
        compute,
        lambda all_zone_data: asa_stats_cache.put_cached_fire_centre_hfi_stats(
            fire_centre_name, run_type.value, run_datetime, for_date, all_zone_data
        ),
    )


def build_firezone_tpi_stats(tpi_stats, tpi_fuel_stats) -> list[FireZoneTPIStats]:
    """Shapes raw TPI rows (source_identifier/pixel_size_metres/valley_bottom/mid_slope/
    upper_slope) plus their matching fuel-area stats into FireZoneTPIStats -- shared between
    the province-wide tpi-stats endpoint and the fire-centre-scoped one in routers/fba.py,
    which differ only in how tpi_stats/tpi_fuel_stats were queried, not in this shaping."""
    hfi_tpi_areas_by_zone = []
    for row in tpi_stats:
        fire_zone_id = row.source_identifier
        square_metres = math.pow(row.pixel_size_metres, 2)
        tpi_fuel_stats_for_zone = [stats for stats in tpi_fuel_stats if stats[2] == fire_zone_id]
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
    return hfi_tpi_areas_by_zone


async def get_tpi_stats(run_type: RunType, run_datetime: datetime, for_date: date) -> TPIResponse:
    """Return the elevation TPI statistics for each advisory threshold for all fire shapes."""

    async def compute() -> TPIResponse:
        async with get_async_read_session_scope() as session:
            tpi_stats = await fetch_tpi_stats_rows(session, run_type, run_datetime, for_date)
            fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
            tpi_fuel_stats = await get_tpi_fuel_areas(session, fuel_type_raster.id)
            hfi_tpi_areas_by_zone = build_firezone_tpi_stats(tpi_stats, tpi_fuel_stats)
        return TPIResponse(firezone_tpi_stats=hfi_tpi_areas_by_zone)

    return await _get_or_compute(
        ("tpi_stats", run_type.value, run_datetime, for_date),
        lambda: asa_stats_cache.get_cached_tpi_stats(run_type.value, run_datetime, for_date),
        compute,
        lambda response: asa_stats_cache.put_cached_tpi_stats(
            run_type.value, run_datetime, for_date, response
        ),
    )


async def get_fire_centre_tpi_stats(
    fire_centre_name: str, run_type: RunType, run_datetime: datetime, for_date: date
) -> FireCentreTPIResponse:
    """Return the elevation TPI statistics for each advisory threshold for one fire centre."""

    async def compute() -> FireCentreTPIResponse:
        async with get_async_read_session_scope() as session:
            tpi_stats_for_centre = await get_centre_tpi_stats(
                session, fire_centre_name, run_type, run_datetime, for_date
            )
            fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)
            tpi_fuel_stats = await get_fire_centre_tpi_fuel_areas(
                session, fire_centre_name, fuel_type_raster.id
            )
            hfi_tpi_areas_by_zone = build_firezone_tpi_stats(tpi_stats_for_centre, tpi_fuel_stats)
        return FireCentreTPIResponse(
            fire_centre_name=fire_centre_name, firezone_tpi_stats=hfi_tpi_areas_by_zone
        )

    return await _get_or_compute(
        ("fire_centre_tpi_stats", fire_centre_name, run_type.value, run_datetime, for_date),
        lambda: asa_stats_cache.get_cached_fire_centre_tpi_stats(
            fire_centre_name, run_type.value, run_datetime, for_date
        ),
        compute,
        lambda response: asa_stats_cache.put_cached_fire_centre_tpi_stats(
            fire_centre_name, run_type.value, run_datetime, for_date, response
        ),
    )
