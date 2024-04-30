""" This module contains pydantic schemas related to SFMS.
"""
from typing import List
from pydantic import BaseModel

class HourlyTIF(BaseModel):
    """ URL of the public hourly tif and it's last modified date in UTC """
    url: str

class HourlyTIFs(BaseModel):
    """ Encapsulates list of hourly tifs as well as metadata about them """
    hourlies: List[HourlyTIF]