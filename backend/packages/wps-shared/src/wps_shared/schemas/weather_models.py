"""This module contains pydandict schemas relating to weather models for the API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModelPredictionDetails(BaseModel):
    prediction_timestamp: datetime
    update_date: datetime
    abbreviation: str
    prediction_run_timestamp: datetime
    station_code: int
    rh_tgl_2: Optional[float] = None
    tmp_tgl_2: Optional[float] = None
    bias_adjusted_temperature: Optional[float] = None
    bias_adjusted_rh: Optional[float] = None
    bias_adjusted_wind_speed: Optional[float] = None
    bias_adjusted_wdir: Optional[float] = None
    precip_24h: Optional[float] = None
    bias_adjusted_precip_24h: Optional[float] = None
    wdir_tgl_10: Optional[float] = None
    wind_tgl_10: Optional[float] = None
