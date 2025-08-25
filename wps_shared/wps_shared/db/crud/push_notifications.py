from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from wps_shared.db.models.push_notifications import (
    PushNotificationDevice,
    PushNotificationDeviceManager,
    PushNotificationLog,
)


def register_device(
    session: Session,
    device_token: str,
    user_id: str = None,
    device_name: str = None,
    device_model: str = None,
    os_version: str = None,
    app_version: str = None,
    latitude: str = None,
    longitude: str = None,
    location_name: str = None,
    environment: str = "production",
) -> PushNotificationDevice:
    """
    Convenience function to register a device
    """
    return PushNotificationDeviceManager.register_or_update_device(
        session=session,
        device_token=device_token,
        user_id=user_id,
        device_name=device_name,
        device_model=device_model,
        os_version=os_version,
        app_version=app_version,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        environment=environment,
    )


def update_device_preferences(
    session: Session,
    device_token: str,
    weather_alerts_enabled: bool = None,
    fire_alerts_enabled: bool = None,
    general_notifications_enabled: bool = None,
    enabled: bool = None,
    environment: str = "production",
) -> Optional[PushNotificationDevice]:
    """
    Update notification preferences for a device
    """
    device = (
        session.query(PushNotificationDevice)
        .filter(
            PushNotificationDevice.device_token == device_token,
            PushNotificationDevice.environment == environment,
        )
        .first()
    )

    if device:
        if weather_alerts_enabled is not None:
            device.weather_alerts_enabled = weather_alerts_enabled
        if fire_alerts_enabled is not None:
            device.fire_alerts_enabled = fire_alerts_enabled
        if general_notifications_enabled is not None:
            device.general_notifications_enabled = general_notifications_enabled
        if enabled is not None:
            device.enabled = enabled

        device.updated_at = func.now()
        session.commit()
        session.refresh(device)
        return device

    return None


def update_device_location(
    session: Session,
    device_token: str,
    latitude: str,
    longitude: str,
    location_name: str = None,
    environment: str = "production",
) -> Optional[PushNotificationDevice]:
    """
    Update location information for a device
    """
    device = (
        session.query(PushNotificationDevice)
        .filter(
            PushNotificationDevice.device_token == device_token,
            PushNotificationDevice.environment == environment,
        )
        .first()
    )

    if device:
        device.latitude = latitude
        device.longitude = longitude
        if location_name is not None:
            device.location_name = location_name
        device.updated_at = func.now()
        session.commit()
        session.refresh(device)
        return device

    return None


def get_devices_by_notification_type(
    session: Session,
    notification_type: str,
    user_ids: List[str] = None,
    environment: str = "production",
) -> List[PushNotificationDevice]:
    """
    Get devices that should receive a specific type of notification
    """
    query = (
        session.query(PushNotificationDevice)
        .filter(PushNotificationDevice.enabled == True)
        .filter(PushNotificationDevice.environment == environment)
    )

    # Filter by notification type preferences
    if notification_type == "weather_alert":
        query = query.filter(PushNotificationDevice.weather_alerts_enabled == True)
    elif notification_type == "fire_alert":
        query = query.filter(PushNotificationDevice.fire_alerts_enabled == True)
    elif notification_type == "general":
        query = query.filter(PushNotificationDevice.general_notifications_enabled == True)

    # Filter by user IDs if provided
    if user_ids:
        query = query.filter(PushNotificationDevice.user_id.in_(user_ids))

    return query.all()


def log_notification(
    session: Session,
    device_token: str,
    user_id: str = None,
    notification_type: str = None,
    title: str = None,
    body: str = None,
    payload: str = None,
    apns_id: str = None,
    status_code: int = None,
    success: bool = False,
    error_message: str = None,
    environment: str = "production",
) -> PushNotificationLog:
    """
    Log a push notification that was sent
    """
    log_entry = PushNotificationLog(
        device_token=device_token,
        user_id=user_id,
        notification_type=notification_type or "unknown",
        title=title,
        body=body,
        data=payload,
        delivered=success,
        delivery_status="success" if success else "failed",
        error_message=error_message,
        environment=environment,
    )

    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)
    return log_entry
