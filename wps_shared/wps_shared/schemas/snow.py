""" This module contains pydantic models related to snow data. """

from datetime import datetime
from pydantic import BaseModel
from wps_shared.db.models.snow import SnowSourceEnum

class ProcessedSnowModel(BaseModel):
    """ The content of a processed snow object"""
    for_date: datetime
    processed_date: datetime
    snow_source: SnowSourceEnum

class ProcessedSnowResponse(BaseModel):
    """ A processed snow response """
    processed_snow: ProcessedSnowModel

