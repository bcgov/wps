""" Bot for loading hourly actual values.
"""
import os
from datetime import timedelta, timezone, datetime
import logging
import sys
from sqlalchemy.exc import IntegrityError
import pandas as pd
from requests import Session
from app import configure_logging, config
import app.db.database
from app.db.crud.observations import save_hourly_actual
from app.db.models.observations import HourlyActual
from app.schemas.observations import WeatherReading
import app.time_utils
from app.fireweather_bot.common import (BaseBot, get_station_names_to_codes, authenticate_session)
from app import wildfire_one
from app.rocketchat_notifications import send_rocketchat_notification

# If running as it's own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def _fix_datetime(source_date):
    """ We want to be explicit about timezones, the csv file gives us a timezone naive date - this is no
    good! We know the date we get is in PST, and we know we need to store it in UTC.
    Furthermore, the csv has discovered another hour. 24. Presumably this means 00 the next day.
    """
    # build a date using year, month and day.
    python_date = datetime.strptime(str(source_date)[:-2], '%Y%m%d')
    # handle the mysterious 24th hour.
    if str(source_date)[-2:] == '24':
        # if it's 24, just push to hour 00 on the next day.
        python_date = python_date + timedelta(days=1)
    else:
        # anything else, we trust.
        python_date = python_date + timedelta(hours=int(str(source_date)[-2:]))
    # but alse need to adjust our time, because it's in PST. PST_UTC_OFFSET is -8, so we have
    # to subtract it, to add 8 hours to our current date.
    # e.g. 12h00 PST, becomes 20h00 UTC
    python_date = python_date - timedelta(hours=app.time_utils.PST_UTC_OFFSET)
    # we've add the offset, so set the timezone to utc:
    python_date = python_date.replace(tzinfo=timezone.utc)
    return python_date


def parse_hourly_actual(station_code: int, hourly_reading: WeatherReading):
    """ Maps WeatherReading to HourlyActual """
    temp_valid = hourly_reading.temperature is not None
    rh_valid = hourly_reading.relative_humidity is not None
    wdir_valid = hourly_reading.wind_direction is not None
    wspeed_valid = hourly_reading.wind_speed is not None
    precip_valid = hourly_reading.precipitation is not None

    return HourlyActual(
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


class HourlyActualsBot(BaseBot):
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

    def process_csv(self, filename: str):
        with open(filename, 'r') as csv_file:
            data_df = pd.read_csv(csv_file)
        station_codes = get_station_names_to_codes()
        # drop any rows where 'display_name' is not found in the station_codes lookup:
        data_df.drop(index=data_df[~data_df['display_name'].isin(
            station_codes.keys())].index, inplace=True)
        # replace 'display_name' column (station name) in df with station_id
        # and rename the column appropriately
        data_df['display_name'].replace(station_codes, inplace=True)
        data_df.rename(columns={'display_name': 'station_code'}, inplace=True)

        # write to database using _session's engine
        with app.db.database.get_write_session_scope() as session:
            # write the data_df to the database one row at a time, so that if data_df contains >=1 rows that
            # are duplicates of what is already in the db, the write won't fail for the unique rows
            # NOTE: iterating over the data_df one Series (row) at a time is ugly, but until pandas is
            # updated with a fix, this is the easiest work-around.
            # See https://github.com/pandas-dev/pandas/issues/15988
            # pylint: disable=unused-variable
            for index, row in data_df.iterrows():
                try:
                    # Go from pandas to a python dict.
                    data = row.to_dict()
                    # Format and fix timestamp, make it be tz aware.
                    data['weather_date'] = _fix_datetime(data['weather_date'])
                    # Throw the data into the model, and persist in the database
                    save_hourly_actual(session, HourlyActual(**data))
                except IntegrityError:
                    logger.info('Skipping duplicate record for %s @ %s',
                                data['station_code'], data['weather_date'])
                    session.rollback()

    def construct_request_body(self):
        return {
            'Start_Date': self._get_start_date(),
            'End_Date': self._get_end_date(),
            'Format': 'CSV',
            'cboFilters': config.get('BC_FIRE_WEATHER_FILTER_ID'),
            'rdoReport': 'OSBH',
        }

    async def run_wfwx(self):
        """ Entry point for running the bot """
        with Session() as session:
            # Authenticate with idir.
            authenticate_session(session)

            station_codes = get_station_names_to_codes()

            start_date = self._get_start_date()
            end_date = self._get_end_date()

            station_hourly_readings = await wildfire_one.get_hourly_readings(
                station_codes, start_date, end_date)

            logger.info("Station hourly readings: %s", station_hourly_readings)

            with app.db.database.get_write_session_scope() as session:
                for station_hourly_reading in station_hourly_readings.result():
                    for hourly_reading in station_hourly_reading.values:
                        save_hourly_actual(session, parse_hourly_actual(
                            station_hourly_reading.station.code, hourly_reading))


async def main():
    """ Makes the appropriate method calls in order to submit a query to the BC FireWeather Phase 1 API
    to get hourly values for all weather stations, downloads the resulting CSV file, writes
    the CSV file to the database, then deletes the local copy of the CSV file.
    """
    try:
        logger.debug('Retrieving hourly actuals...')
        bot = HourlyActualsBot()
        await bot.run_wfwx()
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
