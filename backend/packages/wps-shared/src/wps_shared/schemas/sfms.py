""" This module contains pydantic schemas related to SFMS.
"""
from typing import List, Optional
from pydantic import BaseModel


class HourlyTIF(BaseModel):
    """ URL of the public hourly tif """
    url: str


class HourlyTIFs(BaseModel):
    """ Encapsulates list of hourly tif urls """
    hourlies: List[HourlyTIF]


class StationTemperature(BaseModel):
    """Represents a weather station with temperature and location data for interpolation."""
    code: int
    lat: float
    lon: float
    elevation: float
    temperature: float
    sea_level_temp: Optional[float] = None