""" This module contains pydantic models fpr FWI calc """

from typing import List
from pydantic import BaseModel


class FWIOutput(BaseModel):
    """ FWI calc output """
    datetime: str
    ffmc: float
    dmc: float
    dc: float
    isi: float
    bui: float
    fwi: float


class FWIOutputResponse(BaseModel):
    """ Response for all FWI calc outputs, in a list """
    fwi_outputs: List[FWIOutput]
