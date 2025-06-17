from typing import Dict, List, Optional
from pydantic import BaseModel
from wps_shared.db.models.fire_watch import BurnStatusEnum
from wps_shared.fuel_types import FuelTypeEnum


class FireWatchFireCentre(BaseModel):
    id: int
    name: str


class FireWatchStation(BaseModel):
    code: int
    name: str


class FireWatchInput(BaseModel):
    burn_location: List[float]
    burn_window_end: Optional[str] = None
    burn_window_start: Optional[str] = None
    contact_email: List[str]
    fire_centre: FireWatchFireCentre
    station: FireWatchStation
    status: BurnStatusEnum
    title: str
    # Fuel parameters
    fuel_type: FuelTypeEnum
    percent_conifer: Optional[float] = None
    percent_dead_fir: Optional[float] = None
    percent_grass_curing: Optional[float] = None
    # Weather parameters
    temp_min: float
    temp_preferred: Optional[float] = None
    temp_max: float
    rh_min: float
    rh_preferred: Optional[float] = None
    rh_max: float
    wind_speed_min: float
    wind_speed_preferred: Optional[float] = None
    wind_speed_max: float
    # FWI and FBP parameters
    ffmc_min: Optional[float] = None
    ffmc_preferred: Optional[float] = None
    ffmc_max: Optional[float] = None
    dmc_min: Optional[float] = None
    dmc_preferred: Optional[float] = None
    dmc_max: Optional[float] = None
    dc_min: Optional[float] = None
    dc_preferred: Optional[float] = None
    dc_max: Optional[float] = None
    isi_min: Optional[float] = None
    isi_preferred: Optional[float] = None
    isi_max: Optional[float] = None
    bui_min: Optional[float] = None
    bui_preferred: Optional[float] = None
    bui_max: Optional[float] = None
    hfi_min: float
    hfi_preferred: Optional[float] = None
    hfi_max: float


class FireWatchInputRequest(BaseModel):
    fire_watch: FireWatchInput


class FireWatchOutput(FireWatchInput):
    id: int
    create_timestamp: str
    create_user: str
    update_timestamp: str
    update_user: str


class FireWatchResponse(BaseModel):
    fire_watch: FireWatchOutput


class FireWatchListResponse(BaseModel):
    watch_list: List[FireWatchOutput]


class FireWatchFireCentresResponse(BaseModel):
    fire_centres: List[FireWatchFireCentre]


class BurnForecastOutput(BaseModel):
    id: int
    fire_watch_id: int
    date: str
    temp: float
    rh: float
    wind_speed: float
    ffmc: float
    dmc: float
    dc: float
    isi: float
    bui: float
    hfi: float
    in_prescription: str


class FireWatchOutputBurnForecast(BaseModel):
    fire_watch: FireWatchOutput
    burn_forecasts: List[BurnForecastOutput]


class FireWatchBurnForecastsResponse(BaseModel):
    fire_watch_burn_forecasts: List[FireWatchOutputBurnForecast]
