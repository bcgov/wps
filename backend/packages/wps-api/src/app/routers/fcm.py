import logging

from fastapi import APIRouter, Depends, HTTPException
from wps_shared.auth import asa_authentication_required, audit_asa
from wps_shared.db.crud.fcm import (
    get_device_by_device_id,
    get_notification_settings_for_device,
    save_device_token,
    update_device_token_is_active,
    upsert_notification_settings,
)
from wps_shared.db.database import get_async_write_session_scope
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


@router.post("/register")
async def register_device(request: RegisterDeviceRequest):
    """
    Upsert a device token for a device_id.
    """
    logger.info("/device/register")
    async with get_async_write_session_scope() as session:
        existing = await get_device_by_device_id(session, request.device_id)
        if existing:
            existing.is_active = True
            existing.token = request.token
            existing.updated_at = get_utc_now()
            existing.user_id = request.user_id
            logger.info(f"Updated existing DeviceInfo record for token: {request.token}")
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


@router.post("/unregister", responses={404: {"description": "Token not found."}})
async def unregister_device(request: UnregisterDeviceRequest):
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


@router.get("/notification-settings", responses={404: {"description": "Device not found."}})
async def get_notification_settings(device_id: str) -> NotificationSettingsResponse:
    """
    Return the fire zone IDs the device is subscribed to for notifications.
    """
    logger.info("/device/notification-settings GET")
    async with get_async_write_session_scope() as session:
        fire_shape_ids = await get_notification_settings_for_device(session, device_id)
        return NotificationSettingsResponse(fire_shape_ids=fire_shape_ids)


@router.post("/notification-settings")
async def update_notification_settings(
    request: NotificationSettingsRequest,
) -> NotificationSettingsResponse:
    """
    Replace the notification zone subscriptions for a device.
    """
    logger.info("/device/notification-settings POST")
    async with get_async_write_session_scope() as session:
        await upsert_notification_settings(session, request.device_id, request.fire_shape_ids)
        fire_shape_ids = await get_notification_settings_for_device(session, request.device_id)
        return NotificationSettingsResponse(fire_shape_ids=fire_shape_ids)
