"""Code common to weather model processing"""

from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass
import xarray
from wps_shared.weather_models import ProjectionEnum  # noqa: F401


class ModelEnum(str, Enum):
    """Enumerator for different kinds of supported weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"
    HRDPS = "HRDPS"
    GFS = "GFS"
    NAM = "NAM"
    ECMWF = "ECMWF"


class ModelRunInfo:
    """Information related to a particular model run"""

    def __init__(self, model_enum=None, projection=None, model_run_timestamp=None, prediction_timestamp=None, variable_name=None):
        self.model_enum: Optional[ModelEnum] = model_enum
        self.projection: Optional[ProjectionEnum] = projection
        self.model_run_timestamp: Optional[datetime] = model_run_timestamp
        self.prediction_timestamp: Optional[datetime] = prediction_timestamp
        self.variable_name: Optional[str] = variable_name


@dataclass(frozen=True)
class ModelRunProcessResult:
    model_run_info: ModelRunInfo
    url: str
    data: xarray.Dataset
