"""
FastAPI router for push notification management endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import List, Optional, Dict, Any
import logging
import json

from wps_shared.db.database import get_write_session_scope
from wps_shared.schemas.push_notifications import (
    DeviceLocationRequest,
    DevicePreferencesRequest,
    DeviceRegistrationRequest,
    NotificationResponse,
    SendNotificationRequest,
)
from app.notifications.push_notifications import get_notification_service
from wps_shared.db.crud.push_notifications import (
    register_device,
    update_device_preferences,
    update_device_location,
    get_devices_by_notification_type,
    log_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Dict[str, str])
async def register_device_endpoint(request: DeviceRegistrationRequest):
    """
    Register an iOS device for push notifications

    This endpoint allows iOS devices to register their device tokens
    and associated information for push notifications.
    """
    try:
        with get_write_session_scope() as session:
            device = register_device(
                session=session,
                device_token=request.device_token,
                user_id=request.user_id,
                device_name=request.device_name,
                device_model=request.device_model,
                os_version=request.os_version,
                app_version=request.app_version,
                environment=request.environment,
            )

            logger.info(f"Device registered successfully: {request.device_token}")
            return {"message": "Device registered successfully", "device_id": str(device.id)}

    except Exception as e:
        logger.error(f"Failed to register device {request.device_token}: {e}")
        raise HTTPException(status_code=500, detail="Failed to register device")


@router.put("/preferences", response_model=Dict[str, str])
async def update_preferences_endpoint(request: DevicePreferencesRequest):
    """
    Update notification preferences for a device

    This endpoint allows devices to update their notification preferences,
    such as enabling/disabling specific types of notifications.
    """
    try:
        with get_write_session_scope() as session:
            device = update_device_preferences(
                session=session,
                device_token=request.device_token,
                weather_alerts_enabled=request.weather_alerts_enabled,
                fire_alerts_enabled=request.fire_alerts_enabled,
                general_notifications_enabled=request.general_notifications_enabled,
                enabled=request.enabled,
                environment=request.environment,
            )

            if not device:
                raise HTTPException(status_code=404, detail="Device not found")

            logger.info(f"Preferences updated for device: {request.device_token}")
            return {"message": "Preferences updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preferences for device {request.device_token}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.put("/location", response_model=Dict[str, str])
async def update_location_endpoint(request: DeviceLocationRequest):
    """
    Update location information for a device

    This endpoint allows devices to update their location information
    for geo-targeted notifications.
    """
    try:
        with get_write_session_scope() as session:
            device = update_device_location(
                session=session,
                device_token=request.device_token,
                latitude=request.latitude,
                longitude=request.longitude,
                location_name=request.location_name,
                environment=request.environment,
            )

            if not device:
                raise HTTPException(status_code=404, detail="Device not found")

            logger.info(f"Location updated for device: {request.device_token}")
            return {"message": "Location updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update location for device {request.device_token}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update location")


@router.post("/send", response_model=NotificationResponse)
async def send_notification_endpoint(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    secret: Optional[str] = Header(None, description="API secret for authentication"),
):
    """
    Send push notifications to devices

    This endpoint allows sending push notifications to specific devices or users.
    It can be used by internal services or authenticated external services.
    """
    # TODO: Add proper authentication/authorization
    # For now, using a simple secret header check
    from wps_shared.config import config

    expected_secret = config.get("PUSH_NOTIFICATION_SECRET")
    if expected_secret and secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid authentication")

    try:
        notification_service = get_notification_service()

        # Get target devices
        with get_write_session_scope() as session:
            if request.device_tokens:
                # Send to specific device tokens
                device_tokens = request.device_tokens
            else:
                # Get devices based on notification type and user filters
                devices = get_devices_by_notification_type(
                    session=session,
                    notification_type=request.notification_type,
                    user_ids=request.user_ids,
                    environment=request.environment,
                )
                device_tokens = [device.device_token for device in devices]

        if not device_tokens:
            return NotificationResponse(
                success=False,
                message="No devices found to send notifications to",
                sent_count=0,
                failed_count=0,
            )

        # Send notifications based on type
        if request.notification_type == "weather_alert":
            results = await notification_service.send_weather_alert(
                device_tokens=device_tokens,
                title=request.title,
                body=request.body,
                weather_data=request.custom_data,
            )
        elif request.notification_type == "fire_alert":
            results = await notification_service.send_fire_alert(
                device_tokens=device_tokens,
                title=request.title,
                body=request.body,
                fire_data=request.custom_data,
                high_priority=request.high_priority,
            )
        elif request.notification_type == "general":
            results = await notification_service.send_general_notification(
                device_tokens=device_tokens,
                title=request.title,
                body=request.body,
                custom_data=request.custom_data,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid notification type")

        # Log results in background
        background_tasks.add_task(
            log_notification_results,
            results,
            request.notification_type,
            request.title,
            request.body,
            request.custom_data,
            request.environment,
        )

        # Calculate success/failure counts
        sent_count = sum(1 for result in results if result.get("success"))
        failed_count = len(results) - sent_count

        logger.info(
            f"Sent {request.notification_type} notifications: "
            f"{sent_count} successful, {failed_count} failed"
        )

        return NotificationResponse(
            success=sent_count > 0,
            message=f"Sent notifications to {sent_count} devices, {failed_count} failed",
            sent_count=sent_count,
            failed_count=failed_count,
            details=results if failed_count > 0 else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notifications")


@router.post("/send/weather-alert", response_model=NotificationResponse)
async def send_weather_alert_endpoint(
    title: str,
    body: str,
    background_tasks: BackgroundTasks,
    device_tokens: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    environment: str = "production",
    secret: Optional[str] = Header(None),
):
    """
    Convenience endpoint for sending weather alerts
    """
    request = SendNotificationRequest(
        notification_type="weather_alert",
        title=title,
        body=body,
        device_tokens=device_tokens,
        user_ids=user_ids,
        custom_data=weather_data,
        environment=environment,
    )
    return await send_notification_endpoint(request, background_tasks, secret)


@router.post("/send/fire-alert", response_model=NotificationResponse)
async def send_fire_alert_endpoint(
    title: str,
    body: str,
    background_tasks: BackgroundTasks,
    device_tokens: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
    fire_data: Optional[Dict[str, Any]] = None,
    high_priority: bool = True,
    environment: str = "production",
    secret: Optional[str] = Header(None),
):
    """
    Convenience endpoint for sending fire alerts
    """
    request = SendNotificationRequest(
        notification_type="fire_alert",
        title=title,
        body=body,
        device_tokens=device_tokens,
        user_ids=user_ids,
        custom_data=fire_data,
        high_priority=high_priority,
        environment=environment,
    )
    return await send_notification_endpoint(request, background_tasks, secret)


async def log_notification_results(
    results: List[Dict[str, Any]],
    notification_type: str,
    title: str,
    body: str,
    custom_data: Optional[Dict[str, Any]],
    environment: str,
):
    """
    Background task to log notification results to database
    """
    try:
        with get_write_session_scope() as session:
            for result in results:
                log_notification(
                    session=session,
                    device_token=result.get("device_token", ""),
                    user_id=None,  # TODO: Get user_id from device token lookup
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    payload=json.dumps(custom_data) if custom_data else None,
                    apns_id=result.get("apns_id"),
                    status_code=result.get("status_code", 0),
                    success=result.get("success", False),
                    error_message=str(result.get("error", "")) if result.get("error") else None,
                    environment=environment,
                )

        logger.info(f"Logged {len(results)} notification results")

    except Exception as e:
        logger.error(f"Failed to log notification results: {e}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for push notification service
    """
    try:
        # Basic health check - ensure we can create the notification service
        get_notification_service()
        return {"status": "healthy", "service": "push_notifications"}
    except Exception as e:
        logger.error(f"Push notification service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Push notification service unavailable")
