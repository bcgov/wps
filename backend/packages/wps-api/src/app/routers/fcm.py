import logging

from fastapi import APIRouter, Depends, HTTPException
from wps_shared.auth import asa_authentication_required, audit_asa
from wps_shared.db.crud.fcm import (
    get_device_by_device_id,
    get_device_by_token,
    get_notification_settings_for_device,
    save_device_token,
    update_device_token_is_active,
    upsert_notification_settings,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.fcm import DeviceToken
from wps_shared.utils.time import get_utc_now

from app.fcm.schema import (
    DeviceRequestResponse,
    NotificationSettingsRequest,
    NotificationSettingsResponse,
    RegisterDeviceRequest,
    UnregisterDeviceRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/device",
    dependencies=[Depends(asa_authentication_required), Depends(audit_asa)],
)


@router.post(
    "/register",
    response_model=DeviceRequestResponse,
    response_description="Device registered successfully.",
    responses={409: {"description": "Token is already registered to another device."}},
)
async def register_device(request: RegisterDeviceRequest) -> DeviceRequestResponse:
    """Register or update the FCM token for a device.

    Flow:
    - If the device exists, update its row. This preserves its notification settings.
    - If only the token exists, reuse that row with the new device ID.
    - If neither exists, create a row.
    - If the device and token belong to different rows, return 409.

    The last case should be uncommon, but legacy data or an unusual token reassignment could cause
    it. We cannot safely know which row and notification settings to keep, so the guard prevents us
    from silently deleting or overwriting a user's data. Hopefully we never run into this, it's there
    as a safety measure.
    """
    logger.info("/device/register")
    async with get_async_write_session_scope() as session:
        device_token = await get_device_by_device_id(session, request.device_id, for_update=True)
        token_match = await get_device_by_token(session, request.token, for_update=True)

        if (
            device_token is not None
            and token_match is not None
            and device_token.id != token_match.id
        ):
            logger.error(
                "Device registration conflict: device_id row %s differs from token row %s",
                device_token.id,
                token_match.id,
            )
            raise HTTPException(
                status_code=409,
                detail="Token is already registered to another device",
            )
        elif device_token is None:
            device_token = token_match

        if device_token:
            device_token.is_active = True
            device_token.token = request.token
            device_token.device_id = request.device_id
            device_token.platform = request.platform
            device_token.updated_at = get_utc_now()
            device_token.user_id = request.user_id
            logger.info(f"Updated existing DeviceToken record for token: {request.token}")
        else:
            device_token = DeviceToken(
                user_id=request.user_id,
                device_id=request.device_id,
                token=request.token,
                platform=request.platform,
                is_active=True,
            )
            save_device_token(session, device_token)
            logger.info("Successfully created new DeviceToken record.")
        return DeviceRequestResponse(success=True)


@router.post(
    "/unregister",
    response_model=DeviceRequestResponse,
    response_description="Device unregistered successfully.",
    responses={404: {"description": "Token not found."}},
)
async def unregister_device(request: UnregisterDeviceRequest) -> DeviceRequestResponse:
    """
    Mark a token inactive (e.g., user logged out or uninstalled).
    """
    logger.info("/device/unregister")
    async with get_async_write_session_scope() as session:
        success = await update_device_token_is_active(session, request.token, False)
        if not success:
            logger.error(f"Could not find a record matching the provided token: {request.token}")
            raise HTTPException(status_code=404, detail=f"Token not found: {request.token}")
        return DeviceRequestResponse(success=True)


@router.get(
    "/notification-settings",
    response_model=NotificationSettingsResponse,
    response_description="Notification settings retrieved successfully.",
)
async def get_notification_settings(device_id: str) -> NotificationSettingsResponse:
    """
    Return the fire zone source identifiers the device is subscribed to for notifications.
    """
    logger.info("/device/notification-settings GET")
    async with get_async_read_session_scope() as session:
        fire_zone_source_ids = await get_notification_settings_for_device(session, device_id)
        return NotificationSettingsResponse(fire_zone_source_ids=fire_zone_source_ids)


@router.post(
    "/notification-settings",
    response_model=NotificationSettingsResponse,
    response_description="Notification settings updated successfully.",
    responses={404: {"description": "Device not found."}},
)
async def update_notification_settings(
    request: NotificationSettingsRequest,
) -> NotificationSettingsResponse:
    """
    Replace the notification zone subscriptions for a device.
    """
    logger.info("/device/notification-settings POST")
    async with get_async_write_session_scope() as session:
        found = await upsert_notification_settings(
            session, request.device_id, request.fire_zone_source_ids
        )
        if not found:
            logger.error(
                "Notification settings update for unknown device_id: %s", request.device_id
            )
            raise HTTPException(status_code=404, detail=f"Device not found: {request.device_id}")
        await session.flush()
        fire_zone_source_ids = await get_notification_settings_for_device(
            session, request.device_id
        )
        return NotificationSettingsResponse(fire_zone_source_ids=fire_zone_source_ids)
