from dataclasses import dataclass
from datetime import datetime
import numpy
from numba import vectorize

@dataclass
class TemporalPrecip:
    """Precip values at certain times"""
    timestamp: str
    precip_amount: float | numpy.ndarray
    
    def is_after(self, other) -> bool:
        return self.timestamp > other.timestamp

def generate_24_hour_accumulating_precip_raster(current_time: datetime):
    """
    Given a UTC datetime, grab the raster for that date and compute the 
    """
    pass


def compute_precip_difference(later_precip: TemporalPrecip, earlier_precip: TemporalPrecip):
    """
    Simple function to compute difference between later and earlier precip values
    to be vectorized with numba.
    """
    if not later_precip.is_after(earlier_precip):
        raise ValueError("Later precip value must be after earlier precip value")
    return vectorized_diff(later_precip.precip_amount, earlier_precip.precip_amount)


def _diff(value_a: float, value_b: float):
    return value_a - value_b

vectorized_diff = vectorize(_diff)