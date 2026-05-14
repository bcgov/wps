from typing import List

from pydantic import BaseModel


class FireCentre(BaseModel):
    id: int
    name: str


class FireCentresResponse(BaseModel):
    fire_centres: List[FireCentre]
