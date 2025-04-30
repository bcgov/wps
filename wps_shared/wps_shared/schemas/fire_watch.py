


from typing import List, Optional
from pydantic import BaseModel
from wps_shared.db.models.fire_watch import BurnStatusEnum
from wps_shared.fuel_types import FuelTypeEnum

class FireWatchInput(BaseModel):
    burn_location: List[float]
    burn_window_end: int
    burn_window_start: int
    contact_email: List[str]
    fire_centre: int
    station_code: int
    status: BurnStatusEnum
    title: str
    # Fuel parameters
    fuel_type: FuelTypeEnum
    percent_conifer: Optional[float] = None
    percent_dead_fir: Optional[float] = None
    percent_grass_curing: Optional[float] = None
    # Weather parameters
    temp_min: float
    temp_preferred: float
    temp_max: float
    rh_min: float
    rh_preferred: float
    rh_max: float
    wind_speed_min: float
    wind_speed_preferred: float
    wind_speed_max: float
    # FWI and FBP parameters
    ffmc_min: float
    ffmc_preferred: float
    ffmc_max: float
    dmc_min: float
    dmc_preferred: float
    dmc_max: float
    dc_min: float
    dc_preferred: float
    dc_max: float
    isi_min: float
    isi_preferred: float
    isi_max: float
    bui_min: float
    bui_preferred: float
    bui_max: float
    hfi_min: float
    hfi_preferred: float
    hfi_max: float

class FireWatchOutput(FireWatchInput):
    id: int
    create_timestamp: int
    create_user: str
    update_timestamp: int
    update_user: str

class FireWatchResponse(BaseModel):
    fire_watch: FireWatchOutput

class FireWatchListResponse(BaseModel):
    watch_list: List[FireWatchOutput]