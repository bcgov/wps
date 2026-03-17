import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, UniqueConstraint

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.utils.time import get_utc_now


class PlatformEnum(enum.Enum):
    android = "android"
    ios = "ios"


class DeviceToken(Base):
    """Storage of Firebase Cloud Messaging tokens and client details."""

    __tablename__ = "device_token"
    __table_args__ = {"comment": "Device token management."}
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    user_id = Column(String, nullable=True)  # Optional storage of IDIR for logged in users
    platform = Column(Enum(PlatformEnum), index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TZTimeStamp, default=get_utc_now, nullable=False)
    updated_at = Column(TZTimeStamp, default=get_utc_now, nullable=False)


class NotificationSettings(Base):
    """Per-device zone notification subscriptions."""

    __tablename__ = "notification_settings"
    __table_args__ = (
        UniqueConstraint("device_token_id", "fire_shape_id"),
        {"comment": "Zone-level notification subscriptions per device."},
    )
    id = Column(Integer, primary_key=True, index=True)
    device_token_id = Column(Integer, ForeignKey("device_token.id"), nullable=False, index=True)
    fire_shape_id = Column(Integer, ForeignKey("advisory_shapes.id"), nullable=False, index=True)
    created_at = Column(TZTimeStamp, default=get_utc_now, nullable=False)
