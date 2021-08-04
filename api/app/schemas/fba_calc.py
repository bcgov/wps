""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from enum import Enum
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.schemas.shared import FuelType


# class FuelTypeEnum(str, Enum):
#     """ Enumerator for all valid fuel types. """
#     C1 = 'C1'
#     C2 = 'C2'
#     C3 = 'C3'
#     C4 = 'C4'
#     C5 = 'C5'
#     C6_7 = 'C6 7m CBH'
#     C6_2 = 'C6 2m CBH'
#     C7 = 'C7'
#     D1 = 'D1'
#     D2 = 'D2'
#     M1_75C = 'M1 75% conifer, 25% deciduous'
#     M1_50C = 'M1 50% conifer, 50% deciduous'
#     M1_25C = 'M1 25% conifer, 75% deciduous'
#     M2_75C = 'M2 75% conifer, 25% deciduous'
#     M2_50C = 'M2 50% conifer, 50% deciduous'
#     M2_25C = 'M2 25% conifer, 75% deciduous'
#     M3_30D = 'M3 30% dead fir'
#     M3_60D = 'M3 60% dead fir'
#     M3_100D = 'M3 100% dead fir'
#     M4_30D = 'M4 30% dead fir'
#     M4_60D = 'M4 60% dead fir'
#     M4_100D = 'M4 100% dead fir'
#     O1A = 'O1A'
#     O1B = 'O1B'
#     S1 = 'S1'
#     S2 = 'S2'
#     S3 = 'S3'


class StationRequest(BaseModel):
    """ Request for one individual weather station. """
    station_code: int
    fuel_type: FuelType
    percentage_conifer: Optional[float]
    percentage_dead_balsam_fir: Optional[float]
    grass_cure: Optional[float]
    crown_base_height: Optional[float]
    wind_speed: Optional[float]


class StationListRequest(BaseModel):
    """ Request for a list of stations """
    date: date
    stations: List[StationRequest]


class StationResponse(BaseModel):
    """ Response for one individual weather station.
    NOTE: Most of the values are optional, since if an observation/forecast isn't available,
    there's not much we can do.
    """
    station_code: int
    station_name: str
    zone_code: Optional[str]
    date: date
    elevation: int
    fuel_type: FuelType
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
    critical_hours_hfi_4000: Optional[str] = None
    critical_hours_hfi_10000: Optional[str] = None


class StationsListResponse(BaseModel):
    """ Response for all weather stations, in a list """
    stations: List[StationResponse]
