"""
Processor modules for SFMS interpolation workflows.
"""

from wps_sfms.processors.fwi import (
    BUICalculator,
    DCCalculator,
    DMCCalculator,
    FFMCCalculator,
    FWIFinalCalculator,
    FWIProcessor,
    FWIResult,
    ISICalculator,
)
from wps_sfms.processors.idw import BaseInterpolator, Interpolator
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator

__all__ = [
    "FWIProcessor",
    "FWIResult",
    "FFMCCalculator",
    "DMCCalculator",
    "DCCalculator",
    "ISICalculator",
    "BUICalculator",
    "FWIFinalCalculator",
    "BaseInterpolator",
    "Interpolator",
    "RHInterpolator",
    "TemperatureInterpolator",
    "WindDirectionInterpolator",
    "WindSpeedInterpolator",
]
