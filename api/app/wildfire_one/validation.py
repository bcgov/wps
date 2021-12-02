""" Validation functions that indicate sound response or clean them to our specific standards"""
import math
from app.schemas.observations import WeatherReading


def replace_nones_in_hourly_actual_with_nan(hourly_reading: WeatherReading):
    """ Returns WeatherReading where any and all None values are replaced with math.nan
    in preparation for entry into database. Have to do this because Postgres doesn't
    handle None gracefully (it thinks None != None), but it can handle math.nan ok.
    (See HourlyActual db model) """
    if hourly_reading.temperature is None:
        hourly_reading.temperature = math.nan
    if hourly_reading.relative_humidity is None:
        hourly_reading.relative_humidity = math.nan
    if hourly_reading.precipitation is None:
        hourly_reading.precipitation = math.nan
    if hourly_reading.wind_direction is None:
        hourly_reading.wind_direction = math.nan
    if hourly_reading.wind_speed is None:
        hourly_reading.wind_speed = math.nan
    return hourly_reading
