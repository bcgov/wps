import logging

from fastapi import APIRouter, HTTPException
from wps_shared.db.crud.fcm import (
    get_device_by_token,
    save_device_token,
    update_device_token_is_active,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fcm import DeviceToken
from wps_shared.utils.time import get_utc_now

from app.fcm.schema import DeviceRequestResponse, RegisterDeviceRequest, UnregisterDeviceRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/device")


@router.post("/register")
async def register_device(request: RegisterDeviceRequest):
    """
    Upsert a device token for a user. Called this at app start and whenever FCM token refreshes.
    """
    logger.info("/device/register")
    async with get_async_write_session_scope() as session:
        existing = await get_device_by_token(session, request.token)
        if existing:
            existing.is_active = True
            existing.token = request.token
            existing.updated_at = get_utc_now()
            logger.info(f"Updated existing DeviceInfo record for token: {request.token}")
        else:
            device_token = DeviceToken(
                user_id=request.user_id,
                token=request.token,
                platform=request.platform,
                is_active=True,
            )
            save_device_token(session, device_token)
            logger.info("Successfully created new DeviceToken record.")
        return DeviceRequestResponse(success=True)


@router.delete("/unregister")
async def unregister_device(request: UnregisterDeviceRequest):
    """
    Mark a token inactive (e.g., user logged out or uninstalled).
    """
    logger.info("/device/unregister")
    async with get_async_write_session_scope() as session:
        success = await update_device_token_is_active(session, request.token)
        if not success:
            logger.error(f"Could not find a record matching the provided token: {request.token}")
            raise HTTPException(status_code=404, detail=f"Token not found: {request.token}")
        return DeviceRequestResponse(success=True)
