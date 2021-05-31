""" Bot for loading hourly actual values.
"""
import asyncio
import logging
import math
import os
import sys
from datetime import timedelta
from requests import Session
import app.db.database
import app.time_utils
from app import configure_logging, wildfire_one
from app.db.crud.observations import save_hourly_actual
from app.db.models.observations import HourlyActual
from app.rocketchat_notifications import send_rocketchat_notification
from app.schemas.observations import WeatherReading

# If running as it's own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def parse_hourly_actual(station_code: int, hourly_reading: WeatherReading):
    """ Maps WeatherReading to HourlyActual """
    temp_valid = hourly_reading.temperature is not None
    rh_valid = hourly_reading.relative_humidity is not None and validate_metric(
        hourly_reading.relative_humidity, 0, 100)
    wdir_valid = hourly_reading.wind_direction is not None and validate_metric(
        hourly_reading.wind_direction, 0, 360)
    wspeed_valid = hourly_reading.wind_speed is not None and validate_metric(
        hourly_reading.wind_speed, 0, math.inf)
    precip_valid = hourly_reading.precipitation is not None and validate_metric(
        hourly_reading.precipitation, 0, math.inf)

    is_valid_wfwx = hourly_reading.observation_valid_ind
    if is_valid_wfwx is False:
        logger.warning("Invalid hourly received from WF1 API: %s", hourly_reading.observation_valid_comment)

    is_valid = temp_valid and rh_valid and wdir_valid and wspeed_valid and precip_valid and is_valid_wfwx

    return None if (is_valid is False) else HourlyActual(
        station_code=station_code,
        weather_date=hourly_reading.datetime,
        temp_valid=temp_valid,
        temperature=hourly_reading.temperature,
        rh_valid=rh_valid,
        relative_humidity=hourly_reading.relative_humidity,
        wspeed_valid=wspeed_valid,
        wind_speed=hourly_reading.wind_speed,
        wdir_valid=wdir_valid,
        wind_direction=hourly_reading.wind_direction,
        precip_valid=precip_valid,
        precipitation=hourly_reading.precipitation,
        dewpoint=hourly_reading.dewpoint,
        ffmc=hourly_reading.ffmc,
        isi=hourly_reading.isi,
        fwi=hourly_reading.fwi,
    )


def validate_metric(value, low, high):
    """ Validate metric with it's range of accepted values """
    return low <= value <= high


def get_hourly_readings_synchronously_wfwx(station_codes, start_date, end_date):
    """ Synchronously get hourly readings for given station codes and date range from wfwx """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(wildfire_one.get_hourly_readings(
        station_codes, start_date, end_date))


class HourlyActualsBot():
    """ Bot that downloads the hourly actuals from the wildfire website and stores it in a database. """

    def __init__(self):
        self.now = app.time_utils.get_pst_now()

    def _get_start_date(self) -> int:
        """ Return time N hour ago. E.g. if it's 17h15 now, we'd get YYYYMMDD16. The intention is that
        this bot runs every hour, so if we ask for everything from an hour back, we should be fine.
        However, just to be on the safe side, we're asking for the last three hours - just in case there
        was a station that came in late, or if for whatever reason we missed a run.
        """
        hour_ago = self.now - timedelta(hours=3)
        return int(hour_ago.strftime('%Y%m%d%H'))

    def _get_end_date(self) -> int:
        """ Return now. E.g. if it's 17h15 now, we'd get YYYYMMDD17 """
        return int(self.now.strftime('%Y%m%d%H'))

    async def run_wfwx(self):
        """ Entry point for running the bot """
        with Session() as session:
            session, header = await wildfire_one.get_session_and_auth_header()
            station_codes = await wildfire_one.get_stations(
                session, header, mapper=wildfire_one.station_codes_list_mapper)

            start_date = self._get_start_date()
            end_date = self._get_end_date()

            station_hourly_readings = await wildfire_one.get_hourly_readings(
                station_codes, start_date, end_date)

            logger.info("Station hourly readings: %s", station_hourly_readings)

            with app.db.database.get_write_session_scope() as session:
                for station_hourly_reading in station_hourly_readings:
                    for hourly_reading in station_hourly_reading.values:
                        hourly_actual = parse_hourly_actual(
                            station_hourly_reading.station.code, hourly_reading)
                        if hourly_actual is not None:
                            save_hourly_actual(session, hourly_actual)


def main():
    """ Makes the appropriate method calls in order to submit
    asynchronous queries to the Wildfire 1 API to get hourly values for all weather stations.
    """
    try:
        logger.debug('Retrieving hourly actuals...')
        bot = HourlyActualsBot()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run_wfwx())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    # pylint: disable=broad-except
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error('Failed to retrieve hourly actuals.', exc_info=exception)
        rc_message = ':scream: Encountered error retrieving hourly actuals'
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    main()
