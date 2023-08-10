""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.fire_behaviour.fuel_types import FuelTypeEnum


class StationRequest(BaseModel):
    """ Request for one individual weather station. """
    id: Optional[int] = None
    station_code: int
    fuel_type: FuelTypeEnum
    percentage_conifer: Optional[float] = None
    percentage_dead_balsam_fir: Optional[float] = None
    grass_cure: Optional[float] = None
    crown_base_height: Optional[float] = None
    crown_fuel_load: Optional[float] = None
    wind_speed: Optional[float] = None


class StationListRequest(BaseModel):
    """ Request for a list of stations """
    date: date
    stations: List[StationRequest]


class CriticalHoursHFI(BaseModel):
    """ Object response for critical hours """
    start: float
    end: float


class StationResponse(BaseModel):
    """ Response for one individual weather station.
    NOTE: Most of the values are optional, since if an observation/forecast isn't available,
    there's not much we can do.
    """
    id: Optional[int] = None
    station_code: int
    station_name: str
    zone_code: Optional[str] = None
    elevation: int
    fuel_type: FuelTypeEnum
    status: str
    temp: Optional[float] = None
    rh: Optional[float] = None
    wind_direction: Optional[int] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None
    grass_cure: Optional[float] = None
    fine_fuel_moisture_code: Optional[float] = None
    drought_code: Optional[float] = None
    initial_spread_index: Optional[float] = None
    build_up_index: Optional[float] = None
    duff_moisture_code: Optional[float] = None
    fire_weather_index: Optional[float] = None
    head_fire_intensity: Optional[float] = None
    rate_of_spread: Optional[float] = None
    fire_type: Optional[str] = None
    percentage_crown_fraction_burned: Optional[float] = None
    flame_length: Optional[float] = None
    sixty_minute_fire_size: Optional[float] = None
    thirty_minute_fire_size: Optional[float] = None
    critical_hours_hfi_4000: Optional[CriticalHoursHFI] = None
    critical_hours_hfi_10000: Optional[CriticalHoursHFI] = None


class StationsListResponse(BaseModel):
    """ Response for all weather stations, in a list """
    date: date
    stations: List[StationResponse]
