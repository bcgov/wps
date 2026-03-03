from typing import Optional

from pydantic import BaseModel, Field


class RegisterDeviceRequest(BaseModel):
    user_id: Optional[str] = None
    token: str = Field(..., min_length=10)
    platform: Optional[str] = Field(..., pattern="^(ios|android)?$")

class UnregisterDeviceRequest(BaseModel):
    token: str

class DeviceRequestResponse(BaseModel):
    success: bool

