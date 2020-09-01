import math
from typing import List
from datetime import timedelta
import app.db.database
from app.db.crud import get_hourly_actuals
from app import wildfire_one
from app.schemas import WeatherStationHourlyReadings, WeatherReading


def get(value: object, condition: bool = True):
    """ If the condition is False, or the value is not a number, return None, otherwise
    return the value.
    """
    if not condition or math.isnan(value):
        return None
    return value


async def fetch_hourly_readings_from_db(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
    """ Fetch the hourly readings from the database.
    """
    stations = await wildfire_one.get_stations_by_codes(station_codes)
    session = app.db.database.get_session()
    # by default, we want the last 5 days
    now = app.time_utils.get_utc_now()
    five_days_ago = now - timedelta(days=5)
    readings = get_hourly_actuals(session, station_codes, five_days_ago)

    prev_station_code = None
    station_readings = None
    result = []

    for reading in readings:
        if station_readings is None or reading.station_code != station_readings.station.code:
            station = next(
                station for station in stations if station.code == reading.station_code)
            station_readings = WeatherStationHourlyReadings(station=station, values=[])
            result.append(station_readings)
        weather_reading = WeatherReading(
            datetime=reading.weather_date,
            temperature=get(reading.temperature, reading.temp_valid),
            relative_humidity=get(reading.relative_humidity, reading.rh_valid),
            wind_speed=get(reading.wspeed_valid, reading.wind_speed),
            wind_direction=get(reading.wdir_valid, reading.wind_direction),
            precipitation=get(reading.precip_valid, reading.precipitation),
            dewpoint=get(reading.dewpoint),
            ffmc=get(reading.ffmc),
            isi=get(reading.isi),
            fwi=get(reading.fwi)
        )
        station_readings.values.append(weather_reading)
    return result


async def get_hourly_readings(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    Depending on configuration, will read from WF1 or from local database.
    """
    if wildfire_one.use_wfwx():
        return await wildfire_one.get_hourly_readings(station_codes)
    else:
        # TODO: get it locally
        return await fetch_hourly_readings_from_db(station_codes)
