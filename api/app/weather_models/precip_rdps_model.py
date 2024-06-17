from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Protocol
from abc import abstractmethod
import numpy
from numba import vectorize
from app.utils.s3 import read_into_memory

@dataclass
class TemporalPrecip:
    """Precip values at certain times"""
    timestamp: str
    precip_amount: float | numpy.ndarray
    
    def is_after(self, other) -> bool:
        return self.timestamp > other.timestamp
    
# TODO change when we have stored precip 
RDPS_PRECIP_S3_PREFIX = "sfms/temp/prefix"

def retrieve_previous_precip_raster(timestamp: datetime): 
    """ Retrieve the rasters for computing the 24 hour difference for """
    if timestamp.utcoffset() is None or timestamp.utcoffset().total_seconds != 0.0:
        raise ValueError("timestamp must be a UTC timestamp")
    
    if timestamp.hour < 13:
        ## retrieve yesterday's raster run
        yesterday = timestamp.date() - timedelta(days=1)
        return f'{RDPS_PRECIP_S3_PREFIX}/{yesterday.isoformat()}/12Z.tif'
    
    # otherwise 

async def generate_24_hour_accumulating_precip_raster(current_time: datetime):
    """
    Given a UTC datetime, grab the raster for that date
    and the date for 24 hours before to compute the difference.
    """
    day = current_time.date().isoformat()
    daytime_before = current_time - timedelta(days=1)
    day_before = daytime_before.date().isoformat()
    day_data = await read_into_memory(f'{RDPS_PRECIP_S3_PREFIX}/{day}')
    day_before_data = await read_into_memory(f'{RDPS_PRECIP_S3_PREFIX}/{day_before}')

    later_precip = TemporalPrecip(timestamp=current_time, precip_amount=day_data)
    earlier_precip = TemporalPrecip(timestamp=daytime_before, precip_amount=day_before_data)
    return compute_precip_difference(later_precip, earlier_precip)


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