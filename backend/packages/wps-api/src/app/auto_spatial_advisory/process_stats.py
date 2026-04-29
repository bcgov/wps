import logging
from datetime import date, datetime

from wps_shared.db.crud.auto_spatial_advisory import mark_run_parameter_complete
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum

from app.auto_spatial_advisory.critical_hours import calculate_critical_hours
from app.auto_spatial_advisory.hfi_minimum_wind_speed import process_hfi_min_wind_speed
from app.auto_spatial_advisory.hfi_percent_conifer import process_hfi_percent_conifer
from app.auto_spatial_advisory.process_elevation_hfi import process_hfi_elevation
from app.auto_spatial_advisory.process_fuel_type_area import process_fuel_type_hfi_by_shape
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi
from app.auto_spatial_advisory.process_high_hfi_area import process_high_hfi_area
from app.auto_spatial_advisory.process_zone_status import process_zone_statuses
from app.fcm.notifications import trigger_notifications

logger = logging.getLogger(__name__)


async def process_sfms_hfi_stats(run_type: RunType, run_datetime: datetime, for_date: date):
    raise ValueError("test error to test nats redelivery")
    await process_hfi(run_type, run_datetime, for_date)
    await process_hfi_elevation(run_type, run_datetime, for_date)
    await process_high_hfi_area(run_type, run_datetime, for_date)
    await process_fuel_type_hfi_by_shape(run_type, run_datetime, for_date)
    await process_hfi_min_wind_speed(run_type, run_datetime, for_date)
    await process_hfi_percent_conifer(run_type, run_datetime, for_date)
    await calculate_critical_hours(run_type, run_datetime, for_date)
    await process_zone_statuses(run_type, run_datetime, for_date)

    async with get_async_write_session_scope() as session:
        await mark_run_parameter_complete(session, run_type, run_datetime, for_date)

    try:
        async with get_async_write_session_scope() as session:
            await trigger_notifications(
                session, RunTypeEnum(run_type.value), run_datetime, for_date
            )
    except Exception:
        logger.exception(
            "Failed to send FCM notifications for run_type=%s run_datetime=%s for_date=%s.",
            run_type,
            run_datetime,
            for_date,
        )
