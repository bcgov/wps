""" This module contains pydantic models related to the new formal/non-tinker fba. """

from typing import List, Optional
from pydantic import BaseModel


class FireCenterStation(BaseModel):
    """ A fire weather station has a code, name and geographical coordinate. """
    code: int
    name: str
    zone: Optional[str]


class FireZone(BaseModel):
    """ A fire zone has an id, name(display label) and fire centre alias. """
    id: int
    displayLabel: str
    fireCentreAlias: int


class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    id: str
    name: str
    alias: str
    stations: List[FireCenterStation]
    zones: List[FireZone]


class FireCenterListResponse(BaseModel):
    """ Response for all fire centers, in a list """
    fire_centers: List[FireCentre]
