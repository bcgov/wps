"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.temperature import TemperatureInterpolationProcessor
from wps_sfms.processors.idw import IDWInterpolationProcessor
from wps_sfms.processors.fwi import ActualFWIProcessor

__all__ = [
    "TemperatureInterpolationProcessor",
    "IDWInterpolationProcessor",
    "ActualFWIProcessor",
]
