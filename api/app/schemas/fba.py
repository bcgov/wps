""" This module contains pydantic models related to the new formal/non-tinker fba. """

from typing import List
from pydantic import BaseModel

class PlanningArea(BaseModel):
    """ A planning area (a.k.a. zone) is a small group of stations selected to represent a particular
    zone within a fire centre. """
    name: str
class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    name: str
    planning_areas: List[PlanningArea]

class FireCenterListResponse(BaseModel):
    """ Response for all fire centers, in a list """
    fire_centers: List[FireCentre]
