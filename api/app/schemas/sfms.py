""" This module contains pydantic schemas related to SFMS.
"""
from datetime import datetime
from pydantic import BaseModel


class HourlyTIF(BaseModel):
    """ Data structure for a noon forecast retrieved from BC FireWeather Phase 1 """
    url: str
    timezone: str # timezone tif was uploaded from
    last_modified: datetime
