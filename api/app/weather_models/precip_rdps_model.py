from dataclasses import dataclass
from datetime import datetime, timedelta
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


async def generate_24_hour_accumulating_precip_raster(current_time: datetime):
    """
    Given a UTC datetime, grab the raster for that date
    and the date for 24 hours before to compute the difference.
    """
    (today_key, yesterday_key) = get_raster_keys_to_diff(current_time)
    day_data = await read_into_memory(f'{RDPS_PRECIP_S3_PREFIX}/{today_key}')
    if yesterday_key is None:
        # If we don't have yesterday that means we just return today, that happens
        # when current_time is an anchor hour at 00Z or 12Z and we just return the RDPS
        # model run precip amount.
        return day_data


    yesterday_time = current_time - timedelta(days=1)
    yesterday_data = await read_into_memory(f'{RDPS_PRECIP_S3_PREFIX}/{yesterday_key}')

    later_precip = TemporalPrecip(timestamp=current_time, precip_amount=day_data)
    earlier_precip = TemporalPrecip(timestamp=yesterday_time, precip_amount=yesterday_data)
    return compute_precip_difference(later_precip, earlier_precip)

def get_raster_keys_to_diff(timestamp: datetime): 
    """
    Decides which raster files to use for calculating
    the 24 hour accumulating precip given a timestamp.

    We anchor 00Z and 12Z runs against the RDPS grib rasters,
    for every other hour we calculate the difference between the 
    previous days's computed and stored hour.

    Returns the keys to the tifs in the object store
    """
    if timestamp.utcoffset() is None or timestamp.utcoffset().total_seconds != 0.0:
        raise ValueError("timestamp must be a UTC timestamp")
    
    if timestamp.hour == 0 or timestamp.hour == 12:
        ## Case 1: Anchor hour at 00Z or 12Z, return RDPS model
        today = timestamp - timedelta(hours=1)
        return (f'{RDPS_PRECIP_S3_PREFIX}/{today.isoformat()}/{timestamp.hour}Z.tif')

    ## Case 2: Otherwise calculate the difference with the assumed tifs existing
    # TODO we only have the hour before, can we compare it to the value from the hour from yesterday?
    today = timestamp - timedelta(hours=1)
    yesterday = timestamp - timedelta(days=1)
    return (f'{RDPS_PRECIP_S3_PREFIX}/{yesterday.isoformat()}/{timestamp.hour}Z.tif',
                f'{RDPS_PRECIP_S3_PREFIX}/{today.isoformat()}/{timestamp.hour}Z.tif')


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