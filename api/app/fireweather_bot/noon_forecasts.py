""" This is a bot to pull hourly weather actuals from the BC FireWeather Phase 1 API
for each weather station and store the results (from a CSV file) in our database.
"""
import sys
import logging
import logging.config
from datetime import timedelta, timezone
from sqlalchemy.exc import IntegrityError
import pandas as pd
from app import config, configure_logging
import app.db.database
from app.db.models import NoonForecasts
from app.fireweather_bot.common import BaseBot, get_station_names_to_codes
import app.time_utils


# If running as it's own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

LOGGER = logging.getLogger(__name__)


def _construct_request_body():
    """ Prepare the params to fetch forecast noon-time values from the BC FireWeather Phase 1 API.
    """
    start_date = _get_start_date()
    end_date = _get_end_date()
    LOGGER.debug('requesting noon forecasts from %s to %s',
                 start_date, end_date)
    # Prepare query data:
    return {
        'Start_Date': int(start_date),
        'End_Date': int(end_date),
        'Format': 'CSV',
        'cboFilters': config.get('BC_FIRE_WEATHER_FILTER_ID'),
        'rdoReport': 'OSBD',
    }


def _parse_csv(temp_path: str):
    """ Given a CSV of forecast noon-time weather data for a station, load the CSV into a
    pandas dataframe, then insert the dataframe into the DB. (This 2-step process is
    the neatest way to write CSVs into a DB.)
    """
    with open(temp_path, 'r') as csv_file:
        data_df = pd.read_csv(csv_file)
    station_codes = get_station_names_to_codes()
    # replace 'display_name' column (station name) in df with station_id
    # and rename the column appropriately
    data_df['display_name'].replace(station_codes, inplace=True)
    data_df.rename(columns={'display_name': 'station_code'}, inplace=True)
    # the CSV created by the FireWeather API contains a column indicating if the data
    # is a forecast or an actual value. All rows in our requested CSV should be forecasts,
    # but to make sure, we drop any rows that contain actuals instead of forecasts
    index_names = data_df[data_df['status'] == 'actual'].index
    data_df.drop(index_names, inplace=True)
    # can now delete the 'status' column entirely, since we know it's all forecasts
    # and we don't want to write this column to the DB
    data_df.drop(['status'], axis=1, inplace=True)
    # weather_date is formatted yyyymmdd as an int - need to reformat it as a Timestamp
    # including inserting time - "noon" in BC is assumed to always be 20h00 UTC
    dates = pd.to_datetime(data_df['weather_date'], format='%Y%m%d')
    dates = dates.transform(lambda x: x.replace(hour=20))
    data_df['weather_date'] = dates
    # write to database using _session's engine
    session = app.db.database.get_session()
    # write the data_df to the database one row at a time, so that if data_df contains >=1 rows that are
    # duplicates of what is already in the db, the write won't fail for the unique rows
    # NOTE: iterating over the data_df one Series (row) at a time is ugly, but until pandas is updated
    # with a fix, this is the easiest work-around.
    # See https://github.com/pandas-dev/pandas/issues/15988
    # pylint: disable=unused-variable
    for index, row in data_df.iterrows():
        try:
            row = row.dropna()
            data = row.to_dict()
            # We need to ensure that the timezone is set correctly.
            data['weather_date'] = data['weather_date'].to_pydatetime().replace(tzinfo=timezone.utc)
            session.add(NoonForecasts(**data))
            session.commit()
        except IntegrityError:
            LOGGER.info('Skipping duplicate record')
            session.rollback()


def _get_start_date():
    """ Helper function to get the start date for query (if morning run, use current day; if evening run,
    use tomorrow's date, since we only want forecasts, not actuals)
    Strip out time, we just want yyyymmdd """
    date = ''
    now = app.time_utils.get_utc_now()    # returns time in UTC
    if now.hour == 23:
        # this is the evening run during Pacific Daylight Savings
        date = now + timedelta(days=1)
    else:
        # this is either the morning run, or the evening run during
        # Pacific Standard Time.
        date = now
    # Strip out time, we just want yyyymmdd
    return date.strftime('%Y%m%d')


def _get_end_date():
    """ Helper function to get the end date for query (5 days in future).
    Strip out time, we just want <year><month><date> """
    five_days_ahead = app.time_utils.get_utc_now() + timedelta(days=5)
    return five_days_ahead.strftime('%Y%m%d')


class NoonForecastsBot(BaseBot):
    """ Implementation of class to process noon forecasts. """

    def construct_request_body(self):
        return _construct_request_body()

    def process_csv(self, filename: str):
        _parse_csv(filename)


def main():
    """ Makes the appropriate method calls in order to submit a query to the BC FireWeather Phase 1 API
    to get (up to) 5-day forecasts for all weather stations, downloads the resulting CSV file, writes
    the CSV file to the database, then deletes the local copy of the CSV file.
    """
    try:
        LOGGER.debug('Retrieving noon forecasts...')
        bot = NoonForecastsBot()
        bot.run()
        LOGGER.debug(
            'Finished retrieving noon forecasts for all weather stations.')
        # Exit with 0 - success.
        sys.exit(0)
    # pylint: disable=broad-except
    except Exception as exception:
        # Exit non 0 - failure.
        LOGGER.error('Failed to retrieve noon forecasts.',
                     exc_info=exception)
        sys.exit(1)


if __name__ == '__main__':
    main()
