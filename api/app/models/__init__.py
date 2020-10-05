""" Code common to app.models.fetch """
from enum import Enum


class ModelEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    GDPS = 'GDPS'
    RDPS = 'RDPS'
    HRDPS = 'HRDPS'


class ProjectionEnum(str, Enum):
    """ Enumerator for different projections based on the different
    kinds of weather models
    """
    LATLON_15X_15 = 'latlon.15x.15'
    HIGH_RES_CONTINENTAL = 'ps2.5km'
