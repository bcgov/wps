""" Code common to app.models.fetch """
from enum import Enum


class ModelEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    GDPS = "GDPS"
