"""Code common to weather model processing"""

from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
import xarray

# Key values on ModelRunGridSubsetPrediction.
# Wind direction (wdir_tgl_10_b) is handled slightly differently, so not included here.
SCALAR_MODEL_VALUE_KEYS = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10")


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


@dataclass(frozen=True)
class FireZoneTPIStats:
    """
    Captures fire zone stats of TPI pixels hitting >4K HFI threshold via
    a dictionary, fire_zone_stats, of {source_identifier: {1: X, 2: Y, 3: Z}}, where 1 = valley bottom, 2 = mid slope, 3 = upper slope
    and X, Y, Z are pixel counts at each of those elevation classes respectively.

    Also includes the TPI raster's pixel size in metres.
    """

    model_enum: Optional[ModelEnum]
    projection: Optional[ProjectionEnum]


class ModelRunInfo:
    """Information relation to a particular model run"""

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
