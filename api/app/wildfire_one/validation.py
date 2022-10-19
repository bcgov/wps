""" Validation functions that indicate sound response or clean them to our specific standards"""
import math
from typing import Union
from app.schemas.observations import WeatherReading
from app.schemas.forecasts import NoonForecast


def get_valid_flags(record: Union[WeatherReading, NoonForecast]):
    """ Validate fields and return flags indiciating their validity """
    temp_valid = record.temperature is not None
    rh_valid = record.relative_humidity is not None and validate_metric(
        record.relative_humidity, 0, 100)
    wspeed_valid = record.wind_speed is not None and validate_metric(
        record.wind_speed, 0, math.inf)
    wdir_valid = record.wind_direction is not None and validate_metric(
        record.wind_direction, 0, 360)
    precip_valid = record.precipitation is not None and validate_metric(
        record.precipitation, 0, math.inf)
    return temp_valid, rh_valid, wspeed_valid, wdir_valid, precip_valid


def validate_metric(value, low, high):
    """ Validate metric with it's range of accepted values """
    return low <= value <= high
