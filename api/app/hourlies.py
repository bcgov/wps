from typing import List
import app.db.database
from app import wildfire_one


def fetch_hourly_readings_from_db(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
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
            station_readings = WeatherStationHourlyReadings()
            station_readings.station = next(
                station for station in stations if station.code == reading.station_code)
        weather_reading = WeatherReading()
        station_readings.values.append(weather_reading)


async def get_hourly_readings(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    Depending on configuration, will read from WF1 or from local database.
    """
    if wildfire_one.use_wfwx():
        return await wildfire_one.get_hourly_readings(station_codes)
    else:
        # TODO: get it locally
        return fetch_hourly_readings_from_db(station_codes)
