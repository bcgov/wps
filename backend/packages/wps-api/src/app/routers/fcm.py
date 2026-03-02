from fastapi import APIRouter

from wps_shared.db.crud.fcm import (
    get_device_by_token,
    save_device_token,
    update_device_token_is_active,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fcm import DeviceToken
from wps_shared.utils.time import get_utc_now

import app
from app.fcm.schema import DeviceRequestResponse, RegisterDeviceRequest, UnregisterDeviceRequest

router = APIRouter(
    prefix="/device"
)

@router.post("/register")
async def register_device(request: RegisterDeviceRequest):
    """
    Upsert a device token for a user. Called this at app start and whenever FCM token refreshes.
    """
    async with get_async_write_session_scope() as session:
        existing = await get_device_by_token(session, request.token)
        if existing:
            existing.is_active = True
            existing.token = request.token
            existing.updated_at = get_utc_now()
        else:
            device_token = DeviceToken(
                user_id=request.user_id,
                token=request.token,
                platform=request.platform,
                is_active=True,
            )
            save_device_token(session, device_token)
        return DeviceRequestResponse(success=True)


@router.delete("/unregister")
async def unregister_device(request: UnregisterDeviceRequest):
    """
    Mark a token inactive (e.g., user logged out or uninstalled).
    """
    async with get_async_write_session_scope() as session:
        await update_device_token_is_active(session, request.token)
        return DeviceRequestResponse(success=True)
