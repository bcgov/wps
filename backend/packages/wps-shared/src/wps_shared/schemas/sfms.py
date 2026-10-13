"""This module contains pydantic schemas related to SFMS."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum


class HourlyTIF(BaseModel):
    """URL of the public hourly tif"""

    url: str


class HourlyTIFs(BaseModel):
    """Encapsulates list of hourly tif urls"""

    hourlies: List[HourlyTIF]


class SFMSDaily(BaseModel):
    """Daily SFMS station weather and FWI values."""

    code: int
    for_datetime: datetime
    run_type: RunTypeEnum
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


class SFMSRunBounds(BaseModel):
    """Target-date bounds for completed SFMS runs."""

    year: int
    run_type: RunTypeEnum
    minimum: date
    maximum: date


class FuelCode(BaseModel):
    """One row of the national FBP fuel lookup table, describing a fuel grid value.

    The colour fields are the national table's r, g, b, h, s and l columns.
    """

    grid_value: int
    export_value: int
    descriptive_name: str
    fuel_type: str
    red: int
    green: int
    blue: int
    hue: int
    saturation: int
    lightness: int


class FuelCodesLookup(BaseModel):
    """A fuel lookup table, one row per fuel grid value."""

    fuel_codes: list[FuelCode]
