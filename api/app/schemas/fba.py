""" This module contains pydantic models related to the new formal/non-tinker fba. """

from typing import List
from pydantic import BaseModel

from app.schemas.stations import WeatherStation
class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    id: str
    name: str
    stations: List[WeatherStation]

class FireCenterListResponse(BaseModel):
    """ Response for all fire centers, in a list """
    fire_centers: List[FireCentre]
