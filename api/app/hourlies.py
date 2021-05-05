""" Hourly reading from weather stations ("actuals")
"""
import math
from typing import List
from datetime import datetime, timedelta
import app.db.database
from app.db.crud.observations import get_hourly_actuals
import app.stations
from app import wildfire_one
from app.schemas.observations import WeatherStationHourlyReadings, WeatherReading


def get(value: object, condition: bool = True):
    """ If the condition is False, or the value is not a number, return None, otherwise
    return the value.
    """
    if not condition or value is None or math.isnan(value):
        return None
    return value


async def fetch_hourly_readings_from_db(
        station_codes: List[int],
        time_of_interest: datetime) -> List[WeatherStationHourlyReadings]:
    """ Fetch the hourly readings from the database.
    """
    stations = await app.stations.get_stations_by_codes(station_codes)
    with app.db.database.get_read_session_scope() as session:
        # by default, we want the past 5 days, and if available the next 10 days.
        date_from = time_of_interest - timedelta(days=5)
        # the UI is interested in hourly reading before and after the time of interest.
        date_to = time_of_interest + timedelta(days=10)
        readings = get_hourly_actuals(session, station_codes, date_from, date_to)
        station_readings = None
        result = []

        for reading in readings:
            if station_readings is None or reading.station_code != station_readings.station.code:
                station = next(
                    station for station in stations if station.code == reading.station_code)
                station_readings = WeatherStationHourlyReadings(
                    station=station, values=[])
                result.append(station_readings)
            weather_reading = WeatherReading(
                datetime=reading.weather_date,
                temperature=get(reading.temperature, reading.temp_valid),
                relative_humidity=get(reading.relative_humidity, reading.rh_valid),
                wind_speed=get(reading.wind_speed, reading.wspeed_valid),
                wind_direction=get(reading.wind_direction, reading.wdir_valid),
                precipitation=get(reading.precipitation, reading.precip_valid),
                dewpoint=get(reading.dewpoint),
                ffmc=get(reading.ffmc),
                isi=get(reading.isi),
                fwi=get(reading.fwi)
            )
            station_readings.values.append(weather_reading)
    return result


def _get_five_day_interval(time_of_interest: datetime):
    five_days_past = time_of_interest - timedelta(days=5)

    # Prepare query params and query:
    start_time_stamp = math.floor(five_days_past.timestamp()*1000)
    end_time_stamp = math.floor(time_of_interest.timestamp()*1000)

    return start_time_stamp, end_time_stamp


async def get_hourly_readings(
        station_codes: List[int],
        time_of_interest: datetime) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    Reading 5 days before, and 10 days after the time of interest are returned.
    Depending on configuration, will read from WF1 or from local database.
    """
    start_time_stamp, end_time_stamp = _get_five_day_interval(time_of_interest)

    if wildfire_one.use_wfwx():
        return await wildfire_one.get_hourly_readings(station_codes, start_time_stamp, end_time_stamp)

    return await fetch_hourly_readings_from_db(station_codes, time_of_interest)
