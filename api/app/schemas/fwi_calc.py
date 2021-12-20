""" This module contains pydantic models fpr FWI calc """

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Daily(BaseModel):
    temperature: Optional[float]
    relative_humidity: Optional[float]
    precipitation: Optional[float]
    wind_direction: Optional[float]
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]
    bui: Optional[float]
    isi: Optional[float]
    wind_speed: Optional[float]


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


class FWIActual(BaseModel):
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]
    isi: Optional[float]
    bui: Optional[float]
    fwi: Optional[float]


class FWIAdjusted(BaseModel):
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]
    isi: Optional[float]
    bui: Optional[float]
    fwi: Optional[float]


class FWIOutput(BaseModel):
    """ FWI calc output """
    datetime: datetime
    actual: FWIActual
    adjusted: Optional[FWIAdjusted]


class FWIOutputResponse(BaseModel):
    """ Response for all FWI calc outputs, in a list """
    fwi_outputs: List[FWIOutput]
