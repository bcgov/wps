"""This module contains pydantic schemas related to SFMS."""

from typing import Any, Dict, List
from pydantic import BaseModel


# Optional: Define a Pydantic model to validate GeoJSON data
class GeoJSONFeature(BaseModel):
    type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = None


class FireShapeFeatures(BaseModel):
    features: List[GeoJSONFeature]
