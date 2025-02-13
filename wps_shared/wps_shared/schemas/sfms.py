""" This module contains pydantic schemas related to SFMS.
"""
from typing import List
from pydantic import BaseModel

class HourlyTIF(BaseModel):
    """ URL of the public hourly tif """
    url: str

class HourlyTIFs(BaseModel):
    """ Encapsulates list of hourly tif urls """
    hourlies: List[HourlyTIF]