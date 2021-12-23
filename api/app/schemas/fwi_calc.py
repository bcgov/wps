""" This module contains pydantic models fpr FWI calc """

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Daily(BaseModel):
    temperature: Optional[float]
    status: Optional[str]
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


class MultiFWIInput(BaseModel):
    id: int
    datetime: datetime
    temp: Optional[float]
    rh: Optional[float]
    windDir: Optional[float]
    windSpeed: Optional[float]
    precip: Optional[float]


class FWIIndices(BaseModel):
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]
    isi: Optional[float]
    bui: Optional[float]
    fwi: Optional[float]


class MultiFWIOutput(BaseModel):
    id: int
    datetime: datetime
    status: Optional[str]
    temp: Optional[float]
    rh: Optional[float]
    windDir: Optional[float]
    windSpeed: Optional[float]
    precip: Optional[float]
    actual: FWIIndices
    adjusted: Optional[FWIIndices]


class MultiFWIRequest(BaseModel):
    stationCode: Optional[int]
    inputs: List[MultiFWIInput]


class FWIRequest(BaseModel):
    input: FWIInputParameters
    date: datetime


class FWIOutput(BaseModel):
    """ FWI calc output """
    datetime: datetime
    actual: FWIIndices
    adjusted: Optional[FWIIndices]


class FWIOutputResponse(BaseModel):
    """ Response for all FWI calc outputs, in a list """
    fwi_outputs: List[FWIOutput]


class MultiFWIOutputResponse(BaseModel):
    multi_fwi_outputs: List[MultiFWIOutput]
