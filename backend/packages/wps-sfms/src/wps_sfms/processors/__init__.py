"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.fwi import FWIProcessor, FWIResult
from wps_sfms.processors.idw import Interpolator
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator

__all__ = [
    "FWIProcessor",
    "FWIResult",
    "Interpolator",
    "RHInterpolator",
    "TemperatureInterpolator",
    "WindDirectionInterpolator",
]
