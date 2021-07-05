""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from typing import List
from pydantic import BaseModel


class StationResponse(BaseModel):
    """ Response for one individual weather station. """
    station_code: int
    date: str
    elevation: int
    fuel_type: str
    status: str
    temp: int
    rh: int
    wind_direction: int
    wind_speed: float
    precipitation: float
    grass_cure: int
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
