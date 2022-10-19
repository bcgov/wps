""" This module contains pydantic models fpr FWI calc """

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Daily(BaseModel):
    """ Daily actual schema for computing FWI values """
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
    """Input for basic, single day FWI calculations """
    stationCode: int
    yesterdayFFMC: float
    yesterdayDMC: float
    yesterdayDC: float
    todayTemp: float
    todayRH: float
    todayWindspeed: float
    todayPrecip: float


class MultiFWIInput(BaseModel):
    """Input for multi day FWI calculations """
    id: int
    datetime: datetime
    temp: Optional[float]
    rh: Optional[float]
    windDir: Optional[float]
    windSpeed: Optional[float]
    precip: Optional[float]


class FWIIndices(BaseModel):
    """ Indices for FWI calculations """
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]
    isi: Optional[float]
    bui: Optional[float]
    fwi: Optional[float]


class YesterdayIndices(BaseModel):
    """ Yesterday indices for FWI calculations """
    ffmc: Optional[float]
    dmc: Optional[float]
    dc: Optional[float]


class MultiFWIOutput(BaseModel):
    """ Output for multi day FWI calculations """
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
    """ Request input for multi day FWI calculations """
    stationCode: Optional[int]
    inputs: List[MultiFWIInput]


class FWIRequest(BaseModel):
    """ Request input for single day, basic FWI calculations """
    input: FWIInputParameters
    date: datetime


class FWIOutput(BaseModel):
    """ FWI calc output """
    datetime: datetime
    yesterday: Optional[YesterdayIndices]
    actual: Optional[FWIIndices]
    adjusted: Optional[FWIIndices]


class FWIOutputResponse(BaseModel):
    """ Response for all single day FWI calc outputs, in a list """
    fwi_outputs: List[FWIOutput]


class MultiFWIOutputResponse(BaseModel):
    """ Response for all multi day FWI calc outputs, in a list """
    multi_fwi_outputs: List[MultiFWIOutput]
