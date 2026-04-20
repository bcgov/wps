import logging
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from wps_shared import config
from wps_shared.auth import audit_asa
from wps_shared.run_type import RunType
from wps_shared.schemas.fba import (
    FireCentreInfoResponse,
    HFIStatsResponse,
    LatestSFMSRunParameterRangeResponse,
    LatestSFMSRunParameterResponse,
    ProvincialSummaryResponse,
    SFMSBoundsResponse,
    TPIResponse,
)
from wps_shared.schemas.psu import FireCentresResponse
from wps_shared.utils.time import get_vancouver_now

from app.fcm.schema import (
    DeviceRequestResponse,
    NotificationSettingsRequest,
    NotificationSettingsResponse,
    RegisterDeviceRequest,
    UnregisterDeviceRequest,
)
from app.routers import fba, fcm, psu

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asa-go")


def _validate_not_before_today(*dates: date) -> None:
    # local config to disable date validation
    if config.get("DISABLE_ASA_GO_DATE_VALIDATION") == "True":
        return

    minimum_allowed_date = get_vancouver_now().date()
    past_dates = [value.isoformat() for value in dates if value < minimum_allowed_date]
    if past_dates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"ASA Go only accepts dates on or after {minimum_allowed_date.isoformat()}. "
                f"Rejected: {', '.join(past_dates)}"
            ),
        )


@router.get("/fire-centre-info", response_model=FireCentreInfoResponse)
async def get_fire_centres_and_fire_zone_units():
    return await fba.get_fire_centres_and_fire_zone_units()


@router.get(
    "/provincial-summary/{run_type}/{run_datetime}/{for_date}",
    response_model=ProvincialSummaryResponse,
)
async def get_provincial_summary(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
):
    _validate_not_before_today(for_date)
    return await fba.get_provincial_summary(run_type, run_datetime, for_date)


@router.get("/latest-sfms-run-datetime/{for_date}", response_model=LatestSFMSRunParameterResponse)
async def get_latest_sfms_run_datetime_for_date(
    for_date: date,
):
    _validate_not_before_today(for_date)
    return await fba.get_latest_sfms_run_datetime_for_date(for_date)


@router.get("/sfms-run-bounds", response_model=SFMSBoundsResponse)
async def get_sfms_run_bounds():
    return await fba.get_sfms_run_bounds()


@router.get("/sfms-run-datetimes/{run_type}/{for_date}", response_model=List[datetime])
async def get_run_datetimes_for_date_and_runtype(
    run_type: RunType,
    for_date: date,
):
    _validate_not_before_today(for_date)
    return await fba.get_run_datetimes_for_date_and_runtype(run_type, for_date)


@router.get(
    "/latest-sfms-run-parameters/{start_date}/{end_date}",
    response_model=LatestSFMSRunParameterRangeResponse,
)
async def get_latest_sfms_run_datetime_for_date_range(
    start_date: date,
    end_date: date,
):
    _validate_not_before_today(start_date, end_date)
    return await fba.get_latest_sfms_run_datetime_for_date_range(start_date, end_date)


@router.get(
    "/hfi-stats/{run_type}/{run_datetime}/{for_date}",
    response_model=HFIStatsResponse,
)
async def get_hfi_fuels_data_for_run_parameter(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
):
    _validate_not_before_today(for_date)
    return await fba.get_hfi_fuels_data_for_run_parameter(run_type, run_datetime, for_date)


@router.get(
    "/tpi-stats/{run_type}/{run_datetime}/{for_date}",
    response_model=TPIResponse,
)
async def get_tpi_stats_for_run_parameter(
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
):
    _validate_not_before_today(for_date)
    return await fba.get_tpi_stats_for_run_parameter(run_type, run_datetime, for_date)


@router.get("/fire-centres", response_model=FireCentresResponse)
async def get_all_psu_fire_centres():
    return await psu.get_all_fire_centres()


@router.post("/device/register", response_model=DeviceRequestResponse)
async def register_device(request: RegisterDeviceRequest):
    return await fcm.register_device(request)


@router.post("/device/unregister", response_model=DeviceRequestResponse)
async def unregister_device(request: UnregisterDeviceRequest):
    return await fcm.unregister_device(request)


@router.get("/device/notification-settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(device_id: str):
    return await fcm.get_notification_settings(device_id)


@router.post(
    "/device/notification-settings",
    response_model=NotificationSettingsResponse,
    responses={404: {"description": "Device not found."}},
)
async def update_notification_settings(request: NotificationSettingsRequest):
    return await fcm.update_notification_settings(request)
