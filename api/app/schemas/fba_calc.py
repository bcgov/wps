""" This module contains pydantic models related to Fire Behaviour Advisory Calculator. """

from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class StationRequest(BaseModel):
    """ Request for one individual weather station. """
    station_code: int
    date: Optional[date]  # TODO: remove this date field
    fuel_type: str
    percentage_conifer: Optional[float]
    percentage_dead_balsam_fir: Optional[float]
    grass_cure: Optional[float]
    crown_base_height: Optional[float]


class StationListRequest(BaseModel):
    """ Request for a list of stations """
    date: Optional[date]
    stations: List[StationRequest]


class StationResponse(BaseModel):
    """ Response for one individual weather station.
    NOTE: Most of the values are optional, since if an observation/forecast isn't available,
    there's not much we can do.
    """
    station_code: int
    station_name: str
    date: date
    elevation: int
    fuel_type: str
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
    # FFMC corresponding to an HFI of approx. 4000
    ffmc_for_hfi_4000: Optional[float]
    # HFI when FFMC is equal to value stored in ffmc_for_hfi_4000
    # (this is used bc max. FFMC is 101. In some cases, HFI will never reach 4000 even with FFMC=101)
    hfi_when_ffmc_equals_ffmc_for_hfi_4000: Optional[float]
    # FFMC corresponding to an HFI of approx. 10,000
    ffmc_for_hfi_10000: Optional[float]
    # HFI when FFMC is equal to value stored in ffmc_for_hfi_10000
    # (this is used bc max. FFMC is 101. In some cases, HFI will never reach 10,000 even with FFMC=101)
    hfi_when_ffmc_equals_ffmc_for_hfi_10000: Optional[float]


class StationsListResponse(BaseModel):
    """ Response for all weather stations, in a list """
    stations: List[StationResponse]
