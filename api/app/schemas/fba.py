""" This module contains pydantic models related to the new formal/non-tinker fba. """

from typing import List
from pydantic import BaseModel

from app.db.models.hfi_calc import FireCentre


class FireCenterListResponse(BaseModel):
    """ Response for all fire centers, in a list """
    fire_centers: List[FireCentre]
