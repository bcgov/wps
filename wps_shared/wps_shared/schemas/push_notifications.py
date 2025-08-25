from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DeviceRegistrationRequest(BaseModel):
    """Request model for device registration"""

    device_token: str = Field(..., description="iOS device token for push notifications")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    device_name: Optional[str] = Field(None, description="Device name (e.g., 'John's iPhone')")
    device_model: Optional[str] = Field(None, description="Device model (e.g., 'iPhone 15')")
    os_version: Optional[str] = Field(None, description="iOS version (e.g., '17.0')")
    app_version: Optional[str] = Field(None, description="App version")
    environment: str = Field("production", description="Environment (development/production)")


class DevicePreferencesRequest(BaseModel):
    """Request model for updating device notification preferences"""

    device_token: str = Field(..., description="iOS device token")
    weather_alerts_enabled: Optional[bool] = Field(None, description="Enable weather alerts")
    fire_alerts_enabled: Optional[bool] = Field(None, description="Enable fire alerts")
    general_notifications_enabled: Optional[bool] = Field(
        None, description="Enable general notifications"
    )
    enabled: Optional[bool] = Field(None, description="Enable all notifications")
    environment: str = Field("production", description="Environment")


class DeviceLocationRequest(BaseModel):
    """Request model for updating device location"""

    device_token: str = Field(..., description="iOS device token")
    latitude: str = Field(..., description="Device latitude")
    longitude: str = Field(..., description="Device longitude")
    location_name: Optional[str] = Field(None, description="Human-readable location name")
    environment: str = Field("production", description="Environment")


class SendNotificationRequest(BaseModel):
    """Request model for sending notifications"""

    notification_type: str = Field(
        ..., description="Type of notification (weather_alert, fire_alert, general)"
    )
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    device_tokens: Optional[List[str]] = Field(
        None, description="Specific device tokens (optional)"
    )
    user_ids: Optional[List[str]] = Field(None, description="Specific user IDs (optional)")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Custom data to include")
    high_priority: bool = Field(True, description="Send with high priority")
    environment: str = Field("production", description="Environment")


class NotificationResponse(BaseModel):
    """Response model for notification operations"""

    success: bool
    message: str
    sent_count: Optional[int] = None
    failed_count: Optional[int] = None
    details: Optional[List[Dict[str, Any]]] = None
