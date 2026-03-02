from sqlalchemy import Boolean, Column, Integer, String

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.utils.time import get_utc_now


class DeviceToken(Base):
    """Storage of Firebase Cloud Messaging tokens and client details."""

    __tablename__ = "device_token"
    __table_args__ = {"comment": "Device token management."}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True)  # Optional storage of IDIR for logged in users
    platform = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TZTimeStamp, default=get_utc_now(), nullable=False)
    updated_at = Column(TZTimeStamp, default=get_utc_now(), nullable=False)
