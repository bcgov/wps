""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class StationRequest(BaseModel):
    """ Request for one individual weather station. """
    station_code: int
    date: date
    fuel_type: str
    percentage_conifer: Optional[float]
    percentage_dead_balsam_fir: Optional[float]
    grass_cure: Optional[float]
    crown_base_height: Optional[float]


class StationListRequest(BaseModel):
    """ Request for a list of stations """
    stations: List[StationRequest]


class StationResponse(BaseModel):
    """ Response for one individual weather station. """
    station_code: int
    date: date
    elevation: int
    fuel_type: str
    status: str
    temp: int
    rh: int
    wind_direction: int
    wind_speed: float
    precipitation: float
    grass_cure: Optional[int]
    fine_fuel_moisture_code: float
    drought_code: float
    initial_spread_index: float
    build_up_index: float
    duff_moisture_code: float
    fire_weather_index: float
    head_fire_intensity: float
    rate_of_spread: float
    fire_type: str
    percentage_crown_fraction_burned: int
    flame_length: float
    sixty_minute_fire_size: float
    thirty_minute_fire_size: float


class StationsListResponse(BaseModel):
    """ Response for all weather stations, in a list """
    stations: List[StationResponse]
