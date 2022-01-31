""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from enum import Enum
from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class FuelTypeEnum(str, Enum):
    """ Enumerator for all valid fuel types. """
    C1 = 'C1'
    C2 = 'C2'
    C3 = 'C3'
    C4 = 'C4'
    C5 = 'C5'
    C6 = 'C6'
    C7 = 'C7'
    C7b = 'C7b'
    D1 = 'D1'
    D2 = 'D2'
    M1 = 'M1'
    M2 = 'M2'
    M3 = 'M3'
    M4 = 'M4'
    O1A = 'O1A'
    O1B = 'O1B'
    S1 = 'S1'
    S2 = 'S2'
    S3 = 'S3'


class StationRequest(BaseModel):
    """ Request for one individual weather station. """
    id: Optional[int]
    station_code: int
    fuel_type: FuelTypeEnum
    percentage_conifer: Optional[float]
    percentage_dead_balsam_fir: Optional[float]
    grass_cure: Optional[float]
    crown_base_height: Optional[float]
    crown_fuel_load: Optional[float]
    wind_speed: Optional[float]


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
    id: Optional[int]
    station_code: int
    station_name: str
    zone_code: Optional[str]
    elevation: int
    fuel_type: FuelTypeEnum
    status: str
    temp: Optional[float]
    rh: Optional[float]
    wind_direction: Optional[int]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    grass_cure: Optional[float]
    fine_fuel_moisture_code: Optional[float]
    drought_code: Optional[float]
    initial_spread_index: Optional[float]
    build_up_index: Optional[float]
    duff_moisture_code: Optional[float]
    fire_weather_index: Optional[float]
    head_fire_intensity: Optional[float]
    rate_of_spread: Optional[float]
    fire_type: Optional[str]
    percentage_crown_fraction_burned: Optional[float]
    flame_length: Optional[float]
    sixty_minute_fire_size: Optional[float]
    thirty_minute_fire_size: Optional[float]
    critical_hours_hfi_4000: Optional[CriticalHoursHFI]
    critical_hours_hfi_10000: Optional[CriticalHoursHFI]


class StationsListResponse(BaseModel):
    """ Response for all weather stations, in a list """
    date: date
    stations: List[StationResponse]
