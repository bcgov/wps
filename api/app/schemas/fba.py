""" This module contains pydantic models related to the new formal/non-tinker fba. """

from typing import List, Optional
from pydantic import BaseModel


class FireCenterStation(BaseModel):
    """ A fire weather station has a code, name and geographical coordinate. """
    code: int
    name: str
    zone: Optional[str]


class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    id: str
    name: str
    stations: List[FireCenterStation]


class FireCenterListResponse(BaseModel):
    """ Response for all fire centers, in a list """
    fire_centers: List[FireCentre]


class FireZoneArea(BaseModel):
    """ A zone is a grouping of planning areas within a fire centre. """
    mof_fire_zone_id: int
    threshold: int
    combustible_area: int
    elevated_hfi_area: float
    elevated_hfi_percentage: float


class FireZoneAreaListResponse(BaseModel):
    """ Response for all planning areas, in a list """
    zones: List[FireZoneArea]


class FireZoneHighHfiAreas(BaseModel):
    """ A fire zone and the area exceeding HFI thresholds. """
    mof_fire_zone_id: int
    advisory_area: float
    warn_area: float


class FireZoneHighHfiAreasListResponse(BaseModel):
    """ Response for all fire zones and their areas exceeding high HFI thresholds. """
    zones: List[FireZoneHighHfiAreas]


class HfiThresholdAreaByFuelType(BaseModel):
    """ Total area in sq.m. within HFI threshold for a specific fuel type """
    fuel_type_id: int
    threshold: int
    area: float
