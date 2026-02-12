"""This module contains pydantic schemas related to SFMS."""

from typing import List, Optional
from pydantic import BaseModel


class HourlyTIF(BaseModel):
    """URL of the public hourly tif"""

    url: str


class HourlyTIFs(BaseModel):
    """Encapsulates list of hourly tif urls"""

    hourlies: List[HourlyTIF]


class SFMSDailyActual(BaseModel):
    """Daily Actual"""

    code: int
    lat: float
    lon: float
    elevation: Optional[float] = None
    temperature: Optional[float] = None
    dewpoint: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    ffmc: Optional[float] = None
    dmc: Optional[float] = None
    dc: Optional[float] = None
