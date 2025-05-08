"""Code common to weather model processing"""

from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass
import xarray


class ModelEnum(str, Enum):
    """Enumerator for different kinds of supported weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"
    HRDPS = "HRDPS"
    GFS = "GFS"
    NAM = "NAM"
    ECMWF = "ECMWF"


class ProjectionEnum(str, Enum):
    """Enumerator for different projections based on the different
    kinds of weather models
    """

    LATLON_24X_24 = "latlon.24x.24"
    LATLON_15X_15 = "latlon.15x.15"
    HIGH_RES_CONTINENTAL = "ps2.5km"
    REGIONAL_PS = "ps10km"
    GFS_LONLAT = "lonlat.0.25deg"
    HRDPS_LATLON = "RLatLon0.0225"
    NAM_POLAR_STEREO = "ps32km"
    ECMWF_LATLON = "latlon.0.25deg"


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
