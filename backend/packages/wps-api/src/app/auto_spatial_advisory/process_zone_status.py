import logging
from collections import defaultdict
from datetime import date, datetime
from time import perf_counter

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_spatial_advisory.fuel_type_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.auto_spatial_advisory import (
    get_hfi_area,
    get_hfi_threshold_ids,
    get_run_parameters_id,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryZoneStatus,
    HfiClassificationThresholdEnum,
    RunTypeEnum,
)
from wps_shared.run_type import RunType

logger = logging.getLogger(__name__)


async def advisory_status_already_processed(
    session: AsyncSession, run_param_id: int, fuel_type_raster_id: int
) -> bool:
    stmt = select(
        exists().where(
            AdvisoryZoneStatus.run_parameters == run_param_id,
            AdvisoryZoneStatus.fuel_type_raster_id == fuel_type_raster_id,
        )
    )

    result = await session.execute(stmt)
    return result.scalar()


async def process_zone_statuses(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Entry point for calculating advisory zone statuses based on HFI data.
    """
    logger.info(
        "Processing advisory zone statuses for run type: %s, run datetime: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
    )

    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_param_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        fuel_type_raster = await get_fuel_type_raster_by_year(session, for_date.year)

        if await advisory_status_already_processed(session, run_param_id, fuel_type_raster.id):
            logger.info("Advisory zone statuses already processed.")
            return

        zone_statuses = await calculate_zone_statuses(
            session,
            run_param_id,
            RunType(run_type),
            run_datetime,
            for_date,
            fuel_type_raster.id,
        )

        await store_all_advisory_zone_status(session, zone_statuses)
        delta = perf_counter() - perf_start
        logger.info(f"delta count before and after calculating zone advisory statuses: {delta}")


async def calculate_zone_statuses(
    session: AsyncSession,
    run_parameters_id: int,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    fuel_type_raster_id: int,
) -> list[AdvisoryZoneStatus]:
    thresholds_lut = await get_hfi_threshold_ids(session)
    advisory_id = thresholds_lut[HfiClassificationThresholdEnum.ADVISORY.value]
    warning_id = thresholds_lut[HfiClassificationThresholdEnum.WARNING.value]

    rows = await get_hfi_area(
        session,
        RunTypeEnum(run_type.value),
        run_datetime,
        for_date,
        fuel_type_raster_id,
    )

    # Group by shape_id
    shape_data = defaultdict(lambda: {"combustible_area": 0, "hfi_areas": {}})
    for row in rows:
        shape_data[row.shape_id]["combustible_area"] = row.combustible_area
        shape_data[row.shape_id]["hfi_areas"][row.threshold] = row.hfi_area

    zone_statuses: list[AdvisoryZoneStatus] = []
    for shape_id, data in shape_data.items():
        combustible_area = data["combustible_area"]
        advisory_area = data["hfi_areas"].get(advisory_id, 0)
        warning_area = data["hfi_areas"].get(warning_id, 0)

        advisory_percent = (advisory_area / combustible_area) * 100 if combustible_area > 0 else 0
        warning_percent = (warning_area / combustible_area) * 100 if combustible_area > 0 else 0

        zone_statuses.append(
            AdvisoryZoneStatus(
                run_parameters=run_parameters_id,
                advisory_shape_id=shape_id,
                advisory_percentage=advisory_percent,
                warning_percentage=warning_percent,
                fuel_type_raster_id=fuel_type_raster_id,
            )
        )

    return zone_statuses


async def store_all_advisory_zone_status(
    session: AsyncSession, zone_statuses: list[AdvisoryZoneStatus]
):
    logger.info("Writing advisory zone statuses.")
    session.add_all(zone_statuses)
