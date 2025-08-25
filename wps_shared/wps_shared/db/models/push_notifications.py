"""
Database models for push notification device management
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
import logging

from wps_shared.db.models import Base

logger = logging.getLogger(__name__)


class PushNotificationDevice(Base):
    """
    Model for storing iOS device tokens for push notifications
    """

    __tablename__ = "push_notification_devices"

    id = Column(Integer, primary_key=True, index=True)

    # Device information
    device_token = Column(String(64), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Optional user association
    device_name = Column(String(255), nullable=True)
    device_model = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    app_version = Column(String(50), nullable=True)

    # Notification preferences
    enabled = Column(Boolean, default=True, nullable=False)
    weather_alerts_enabled = Column(Boolean, default=True, nullable=False)
    fire_alerts_enabled = Column(Boolean, default=True, nullable=False)
    general_notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Location preferences (for geo-targeted notifications)
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    location_name = Column(String(255), nullable=True)

    # Metadata
    registered_at = Column(DateTime, default=func.now(), nullable=False)
    last_seen_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Environment (development/production)
    environment = Column(String(20), default="production", nullable=False)

    # Ensure unique device tokens per environment
    __table_args__ = (
        UniqueConstraint("device_token", "environment", name="unique_device_token_environment"),
    )


class PushNotificationLog(Base):
    """
    Model for logging sent push notifications
    """

    __tablename__ = "push_notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Device and notification info
    device_token = Column(String(64), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)

    # Notification content
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    data = Column(Text, nullable=True)  # JSON string for additional data

    # Delivery status
    sent_at = Column(DateTime, default=func.now(), nullable=False)
    delivered = Column(Boolean, default=False, nullable=False)
    delivery_status = Column(String(50), nullable=True)  # success, failed, invalid_token
    error_message = Column(Text, nullable=True)

    # Environment
    environment = Column(String(20), default="production", nullable=False)

    @classmethod
    def create_log(
        cls,
        session: Session,
        device_token: str,
        notification_type: str,
        title: str = None,
        body: str = None,
        data: str = None,
        user_id: str = None,
        environment: str = "production",
    ) -> "PushNotificationLog":
        """
        Create a new notification log entry
        """
        log_entry = cls(
            device_token=device_token,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            environment=environment,
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)
        return log_entry

    @classmethod
    def mark_delivered(
        cls,
        session: Session,
        log_id: int,
        delivered: bool = True,
        delivery_status: str = "success",
        error_message: str = None,
    ) -> Optional["PushNotificationLog"]:
        """
        Update delivery status for a notification log
        """
        log_entry = session.query(cls).filter(cls.id == log_id).first()
        if log_entry:
            log_entry.delivered = delivered
            log_entry.delivery_status = delivery_status
            log_entry.error_message = error_message
            session.commit()
            session.refresh(log_entry)
            return log_entry
        return None

    @classmethod
    def get_recent_logs(
        cls,
        session: Session,
        device_token: str = None,
        user_id: str = None,
        limit: int = 50,
        environment: str = "production",
    ) -> List["PushNotificationLog"]:
        """
        Get recent notification logs for a device or user
        """
        query = session.query(cls).filter(cls.environment == environment)

        if device_token:
            query = query.filter(cls.device_token == device_token)
        if user_id:
            query = query.filter(cls.user_id == user_id)

        return query.order_by(cls.sent_at.desc()).limit(limit).all()

    @classmethod
    def get_failure_stats(
        cls,
        session: Session,
        environment: str = "production",
        hours_back: int = 24,
    ) -> dict:
        """
        Get statistics on notification delivery failures
        """
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        query = (
            session.query(cls)
            .filter(cls.environment == environment)
            .filter(cls.sent_at >= cutoff_time)
        )

        total_sent = query.count()
        failed_deliveries = query.filter(cls.delivered == False).count()
        invalid_tokens = query.filter(cls.delivery_status == "invalid_token").count()

        return {
            "total_sent": total_sent,
            "failed_deliveries": failed_deliveries,
            "invalid_tokens": invalid_tokens,
            "success_rate": (total_sent - failed_deliveries) / total_sent if total_sent > 0 else 0,
            "hours_analyzed": hours_back,
        }


# Helper functions for device management
class PushNotificationDeviceManager:
    """
    Helper class for managing push notification devices
    """

    @staticmethod
    def register_or_update_device(
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
        Register a new device or update an existing one
        """
        existing_device = (
            session.query(PushNotificationDevice)
            .filter(
                PushNotificationDevice.device_token == device_token,
                PushNotificationDevice.environment == environment,
            )
            .first()
        )

        if existing_device:
            # Update existing device
            if user_id is not None:
                existing_device.user_id = user_id
            if device_name is not None:
                existing_device.device_name = device_name
            if device_model is not None:
                existing_device.device_model = device_model
            if os_version is not None:
                existing_device.os_version = os_version
            if app_version is not None:
                existing_device.app_version = app_version
            if latitude is not None:
                existing_device.latitude = latitude
            if longitude is not None:
                existing_device.longitude = longitude
            if location_name is not None:
                existing_device.location_name = location_name

            existing_device.last_seen_at = func.now()
            existing_device.updated_at = func.now()

            session.commit()
            session.refresh(existing_device)
            return existing_device
        else:
            # Create new device
            new_device = PushNotificationDevice(
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
            session.add(new_device)
            session.commit()
            session.refresh(new_device)
            return new_device

    @staticmethod
    def get_active_devices(
        session: Session,
        environment: str = "production",
        user_id: str = None,
    ) -> List[PushNotificationDevice]:
        """
        Get all active devices for push notifications
        """
        query = (
            session.query(PushNotificationDevice)
            .filter(PushNotificationDevice.enabled == True)
            .filter(PushNotificationDevice.environment == environment)
        )

        if user_id:
            query = query.filter(PushNotificationDevice.user_id == user_id)

        return query.all()

    @staticmethod
    def disable_device(
        session: Session,
        device_token: str,
        environment: str = "production",
    ) -> bool:
        """
        Disable a device for push notifications
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
            device.enabled = False
            device.updated_at = func.now()
            session.commit()
            return True

        return False
