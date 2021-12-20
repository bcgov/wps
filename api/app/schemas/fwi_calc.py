""" This module contains pydantic models fpr FWI calc """

from datetime import datetime
from typing import List
from pydantic import BaseModel


class FWIInputParameters(BaseModel):
    stationCode: int
    yesterdayFFMC: float
    yesterdayDMC: float
    yesterdayDC: float
    todayTemp: float
    todayRH: float
    todayWindspeed: float
    todayPrecip: float


class FWIRequest(BaseModel):
    input: FWIInputParameters
    date: datetime


class FWIOutput(BaseModel):
    """ FWI calc output """
    datetime: datetime
    ffmc: float
    dmc: float
    dc: float
    isi: float
    bui: float
    fwi: float


class FWIOutputResponse(BaseModel):
    """ Response for all FWI calc outputs, in a list """
    fwi_outputs: List[FWIOutput]
