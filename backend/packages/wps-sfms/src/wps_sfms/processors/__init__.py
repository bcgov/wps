"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.temperature import TemperatureInterpolationProcessor
from wps_sfms.processors.precipitation import PrecipitationInterpolationProcessor

__all__ = [
    "TemperatureInterpolationProcessor",
    "PrecipitationInterpolationProcessor",
]
