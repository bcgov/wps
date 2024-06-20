from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy
from numba import vectorize
from app.utils.s3 import read_into_memory
from app.weather_models import ModelEnum


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
    day_data = await read_into_memory(f"{RDPS_PRECIP_S3_PREFIX}/{today_key}")
    if yesterday_key is None:
        # If we don't have yesterday that means we just return today, that happens
        # when current_time is an anchor hour at 00Z or 12Z and we just return the RDPS
        # model run precip amount.
        return day_data

    yesterday_time = current_time - timedelta(days=1)
    yesterday_data = await read_into_memory(f"{RDPS_PRECIP_S3_PREFIX}/{yesterday_key}")

    later_precip = TemporalPrecip(timestamp=current_time, precip_amount=day_data)
    earlier_precip = TemporalPrecip(timestamp=yesterday_time, precip_amount=yesterday_data)
    return compute_precip_difference(later_precip, earlier_precip)


def get_raster_keys_to_diff(timestamp: datetime):
    """
    To maintain the invariant that only the same model runs are diffed, we need to grab the latest
    model run that has data greater than 24 hours ago, but less than 36 hours ago.
    """
    target_model_run_date = timestamp - timedelta(hours=24)
    target_date_key = f"{target_model_run_date.year}-{target_model_run_date.month}-{target_model_run_date.day}"
    # From earlier model run, get the keys for 24 hours before timestamp and the timestamp to perform the diff
    # TODO figure out the filename, for model runs we use the RDPS naming, what do we use for intermediate diffs?
    earlier_key = f"weather_models/{ModelEnum.RDPS.lower()}/{target_date_key}/{target_model_run_date.hour:02d}/precip/todo-filename"
    later_key = f"weather_models/{ModelEnum.RDPS.lower()}/{target_date_key}/{timestamp.hour:02d}/precip/todo-filename"
    return (earlier_key, later_key)


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
