"""This module contains pydantic models related to the new formal/non-tinker fba."""

from typing import List, Optional
from pydantic import BaseModel


class FireCenterStation(BaseModel):
    """A fire weather station has a code, name and geographical coordinate."""

    code: int
    name: str
    zone: Optional[str] = None


class FireCentre(BaseModel):
    """The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it."""

    id: str
    name: str
    stations: List[FireCenterStation]


class FireCenterListResponse(BaseModel):
    """Response for all fire centers, in a list"""

    fire_centers: List[FireCentre]


class FireShapeArea(BaseModel):
    """A zone is a grouping of planning areas within a fire centre."""

    fire_shape_id: int
    threshold: Optional[int] = None
    combustible_area: float
    elevated_hfi_area: Optional[float] = None
    elevated_hfi_percentage: float


class FireShapeAreaListResponse(BaseModel):
    """Response for all planning areas, in a list"""

    shapes: List[FireShapeArea]


class FireShapeAreaDetail(FireShapeArea):
    """Summary information about an advisory shape"""

    fire_shape_name: str
    fire_centre_name: str


class ProvincialSummaryResponse(BaseModel):
    provincial_summary: List[FireShapeAreaDetail]


class FireShapeHighHfiAreas(BaseModel):
    """A fire zone and the area exceeding HFI thresholds."""

    fire_shape_id: int
    advisory_area: float
    warn_area: float


class FireShapeHighHfiAreasListResponse(BaseModel):
    """Response for all fire zones and their areas exceeding high HFI thresholds."""

    zones: List[FireShapeHighHfiAreas]


class HfiThresholdAreaByFuelType(BaseModel):
    """Total area in sq.m. within HFI threshold for a specific fuel type"""

    fuel_type_id: int
    threshold: int
    area: float


class HfiThreshold(BaseModel):
    """An HFI Classification threshold"""

    id: int
    name: str
    description: str


class SFMSFuelType(BaseModel):
    """Data for fuel types used by SFMS system to calculate HFI spatially."""

    fuel_type_id: int
    fuel_type_code: str
    description: str


class AdvisoryCriticalHours(BaseModel):
    """Critical Hours for an advisory."""

    start_time: float
    end_time: float


class ClassifiedHfiThresholdFuelTypeArea(BaseModel):
    """Collection of data objects recording the area within an advisory shape
    that meets a particular HfiThreshold for a specific SFMSFuelType
    """

    fuel_type: SFMSFuelType
    threshold: HfiThreshold
    critical_hours: AdvisoryCriticalHours
    area: float


class FireZoneElevationStats(BaseModel):
    """Basic elevation statistics for a firezone"""

    minimum: float
    quartile_25: float
    median: float
    quartile_75: float
    maximum: float


class FireZoneTPIStats(BaseModel):
    """Classified TPI areas of the fire zone contributing to the HFI >4k. Each area is in square metres."""

    fire_zone_id: int
    valley_bottom: int
    mid_slope: int
    upper_slope: int


class FireZoneElevationStatsByThreshold(BaseModel):
    """Elevation statistics for a firezone by threshold"""

    threshold: int
    elevation_info: FireZoneElevationStats


class FireZoneElevationStatsListResponse(BaseModel):
    """Response for a firezone that includes elevation statistics by threshold for the run parameters of interest"""

    hfi_elevation_info: List[FireZoneElevationStatsByThreshold]
