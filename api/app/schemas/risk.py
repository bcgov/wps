"""This module contains pydantic schemas related to SFMS."""

from typing import Any, Dict, List
from pydantic import BaseModel
from datetime import datetime


# Optional: Define a Pydantic model to validate GeoJSON data
class GeoJSONFeature(BaseModel):
    type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = None


class FireShapeFeatures(BaseModel):
    features: List[GeoJSONFeature]


class GrowInput(BaseModel):
    fire_perimeter: FireShapeFeatures
    hotspots: FireShapeFeatures
    time_of_interest: datetime


class ComputeInput(BaseModel):
    values: FireShapeFeatures
    hotspots: FireShapeFeatures


class FireShapeStation(BaseModel):
    """
    Representative station for a fire perimeter
    """

    fire_number: str
    station_code: int


class FireShapeStations(BaseModel):
    """
    List of representative stations for fire perimeters
    """

    representative_stations: List[FireShapeStation]
