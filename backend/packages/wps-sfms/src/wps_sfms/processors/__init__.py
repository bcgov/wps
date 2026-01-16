"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.temperature import TemperatureInterpolationProcessor
from wps_sfms.processors.weather import InterpolationProcessor

__all__ = [
    "TemperatureInterpolationProcessor",
    "InterpolationProcessor",
]
