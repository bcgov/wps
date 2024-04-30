""" This module contains pydantic schemas related to SFMS.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel

class HourlyTIF(BaseModel):
    """ URL of the public hourly tif and it's last modified date in UTC """
    url: str
    last_modified: datetime

class HourlyTIFs(BaseModel):
    """ Encapsulates list of hourly tifs as well as metadata about them """
    timezone: str # timezone the tifs were uploaded in
    hourlies: List[HourlyTIF]