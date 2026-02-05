"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.temperature import TemperatureInterpolationProcessor
from wps_sfms.processors.idw import IDWInterpolationProcessor

__all__ = [
    "TemperatureInterpolationProcessor",
    "IDWInterpolationProcessor",
]
