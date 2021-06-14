""" This module contains pydandict schemas the HFI Calculator.
"""
from typing import List, Union
from pydantic import BaseModel


class StationDaily(BaseModel):
    """ Station Daily metrics for HFI daily table """
    code: Union[int, None] = None
    elevation: Union[float, None] = None
    status: Union[str, None] = None
    temperature: Union[float, None] = None
    relative_humidity: Union[float, None] = None
    wind_speed: Union[float, None] = None
    wind_direction: Union[float, None] = None
    grass_cure_percentage: Union[float, None] = None
    precipitation: Union[float, None] = None
    ffmc: Union[float, None] = None
    dmc: Union[float, None] = None
    dc: Union[float, None] = None
    isi: Union[float, None] = None
    bui: Union[float, None] = None
    fwi: Union[float, None] = None
    danger_cl: Union[int, None] = None
    fbp_fuel_type: Union[str, None] = None
    observation_valid: Union[bool, None] = None
    observation_valid_comment: Union[str, None] = None


class StationDailyResponse(BaseModel):
    """ Response that includes list of station daily data."""
    dailies: List[StationDaily]
