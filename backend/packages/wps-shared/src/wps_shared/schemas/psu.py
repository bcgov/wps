from typing import List

from pydantic import BaseModel


class PSUFireCentre(BaseModel):
    id: int
    name: str


class FireCentresResponse(BaseModel):
    fire_centres: List[PSUFireCentre]
