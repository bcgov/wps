""" Code common to app.weather_models.fetch """
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# Key values on ModelRunGridSubsetPrediction.
# Wind direction (wdir_tgl_10_b) is handled slightly differently, so not included here.
SCALAR_MODEL_VALUE_KEYS = ('tmp_tgl_2', 'rh_tgl_2', 'wind_tgl_10')


class ModelEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    GDPS = 'GDPS'
    RDPS = 'RDPS'
    HRDPS = 'HRDPS'
    GFS = 'GFS'
    NAM = 'NAM'


class ProjectionEnum(str, Enum):
    """ Enumerator for different projections based on the different
    kinds of weather models
    """
    LATLON_24X_24 = 'latlon.24x.24'
    LATLON_15X_15 = 'latlon.15x.15'
    HIGH_RES_CONTINENTAL = 'ps2.5km'
    REGIONAL_PS = 'ps10km'
    GFS_LONLAT = 'lonlat.0.25deg'
    HRDPS_LATLON = 'RLatLon0.0225'
    NAM_POLAR_STEREO = 'ps32km'