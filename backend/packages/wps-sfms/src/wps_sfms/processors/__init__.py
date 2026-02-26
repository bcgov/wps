"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.fwi import FWIProcessor, FWIResult
from wps_sfms.processors.idw import IDWInterpolationProcessor
from wps_sfms.processors.relative_humidity import RHInterpolationProcessor
from wps_sfms.processors.temperature import TemperatureInterpolationProcessor

__all__ = [
    "FWIProcessor",
    "FWIResult",
    "IDWInterpolationProcessor",
    "RHInterpolationProcessor",
    "TemperatureInterpolationProcessor",
]
