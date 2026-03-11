from typing import Optional

from pydantic import BaseModel, Field


class RegisterDeviceRequest(BaseModel):
    user_id: Optional[str] = None
    device_id: str
    token: str = Field(..., min_length=10)
    platform: str = Field(..., pattern="^(ios|android)$")

class UnregisterDeviceRequest(BaseModel):
    token: str = Field(..., min_length=10)

class DeviceRequestResponse(BaseModel):
    success: bool

