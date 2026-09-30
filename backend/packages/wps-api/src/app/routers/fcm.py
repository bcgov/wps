import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from wps_shared.auth import asa_authentication_required, audit_asa
from wps_shared.db.crud.fcm import (
    DeviceTokenConflictError,
    get_device_token_for_registration,
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
    responses={409: {"description": "Token is already registered to another device."}},
)
async def register_device(request: RegisterDeviceRequest):
    """Register or update the FCM token for a device.

    Flow:
    - Find and lock rows matching the incoming device ID or token.
    - If neither value matches, create a new row.
    - If one row matches either or both values, update that row. This handles FCM token rotation and
      iOS development installs that reuse a token with a new device ID while preserving settings.
    - If the device ID and token match two different rows, return 409. We cannot safely choose which
      row and notification settings to keep, so the conflict guard prevents silent data loss.
    - If a concurrent request inserts the same token between our lookup and insert (FOR UPDATE
      can't lock a row that doesn't exist yet), update the row it created instead.
    """
    logger.info("/device/register")
    async with get_async_write_session_scope() as session:
        existing_row = await _lock_registration_row(session, request)

        if existing_row is None:
            new_device_token = DeviceToken(
                user_id=request.user_id,
                device_id=request.device_id,
                token=request.token,
                platform=request.platform,
                is_active=True,
            )
            try:
                async with session.begin_nested():
                    save_device_token(session, new_device_token)
                logger.info("Successfully created new DeviceToken record.")
                return DeviceRequestResponse(success=True)
            except IntegrityError:
                existing_row = await _lock_registration_row(session, request)
                if existing_row is None:
                    raise
                logger.info("Token registered concurrently, updating that row instead.")

        existing_row.is_active = True
        existing_row.token = request.token
        existing_row.device_id = request.device_id
        existing_row.platform = request.platform
        existing_row.updated_at = get_utc_now()
        existing_row.user_id = request.user_id
        logger.info(f"Updated existing DeviceToken record for token: {request.token}")
        return DeviceRequestResponse(success=True)


async def _lock_registration_row(session, request: RegisterDeviceRequest) -> DeviceToken | None:
    try:
        return await get_device_token_for_registration(session, request.device_id, request.token)
    except DeviceTokenConflictError as exc:
        logger.error("%s", exc)
        raise HTTPException(
            status_code=409,
            detail="Token is already registered to another device",
        ) from exc


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


@router.get("/notification-settings")
async def get_notification_settings(device_id: str) -> NotificationSettingsResponse:
    """
    Return the fire zone source identifiers the device is subscribed to for notifications.
    """
    logger.info("/device/notification-settings GET")
    async with get_async_read_session_scope() as session:
        fire_zone_source_ids = await get_notification_settings_for_device(session, device_id)
        return NotificationSettingsResponse(fire_zone_source_ids=fire_zone_source_ids)


@router.post("/notification-settings", responses={404: {"description": "Device not found."}})
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
