from typing import List
import app.db.database
from app import wildfire_one


def fetch_hourly_readings_from_db(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
    """ Fetch the hourly readings from the database.
    """
    session = app.db.database.get_session()


async def get_hourly_readings(station_codes: List[int]) -> List[WeatherStationHourlyReadings]:
    """ Get the hourly readings for the list of station codes provided.
    Depending on configuration, will read from WF1 or from local database.
    """
    if wildfire_one.use_wfwx():
        return await wildfire_one.get_hourly_readings(station_codes)
    else:
        # TODO: get it locally
        return fetch_hourly_readings_from_db(station_codes)
