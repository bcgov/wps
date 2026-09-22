import logging
from datetime import date, datetime

from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.auto_spatial_advisory import mark_run_parameter_complete
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.geospatial.geospatial import clear_gdal_runtime_cache

from app.auto_spatial_advisory.critical_hours import calculate_critical_hours
from app.auto_spatial_advisory.fire_zone_raster import validate_fire_zone_raster
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
    async with get_async_read_session_scope() as session:
        await validate_fire_zone_raster(session)

    await process_hfi(run_type, run_datetime, for_date)
    await process_hfi_elevation(run_type, run_datetime, for_date)
    await process_high_hfi_area(run_type, run_datetime, for_date)
    await process_fuel_type_hfi_by_shape(run_type, run_datetime, for_date)
    await process_hfi_min_wind_speed(run_type, run_datetime, for_date)
    try:
        await process_hfi_percent_conifer(run_type, run_datetime, for_date)
    except Exception as exc:
        logger.exception(
            "Failed to process HFI percent conifer for run_type=%s run_datetime=%s "
            "for_date=%s; continuing without percent-conifer statistics.",
            run_type,
            run_datetime,
            for_date,
        )
        send_chatops_notification(
            "ASA percent-conifer statistics failed; continuing without percent-conifer data "
            f"for run_type={run_type} run_datetime={run_datetime} for_date={for_date}",
            exc,
            severity="critical",
        )
    await calculate_critical_hours(run_type, run_datetime, for_date)
    await process_zone_statuses(run_type, run_datetime, for_date)

    clear_gdal_runtime_cache()

    async with get_async_write_session_scope() as session:
        completed_now = await mark_run_parameter_complete(session, run_type, run_datetime, for_date)

    if not completed_now:
        logger.info(
            "Skipping FCM notifications because the run was already complete for "
            "run_type=%s run_datetime=%s for_date=%s.",
            run_type,
            run_datetime,
            for_date,
        )
        return

    try:
        async with get_async_write_session_scope() as session:
            await trigger_notifications(
                session, RunTypeEnum(run_type.value), run_datetime, for_date
            )
    except Exception as exc:
        logger.exception(
            "Failed to send FCM notifications for run_type=%s run_datetime=%s for_date=%s.",
            run_type,
            run_datetime,
            for_date,
        )
        send_chatops_notification(
            "ASA FCM notifications failed "
            f"for run_type={run_type} run_datetime={run_datetime} for_date={for_date}",
            exc,
            severity="critical",
        )
