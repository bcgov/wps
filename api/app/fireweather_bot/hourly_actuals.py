""" Bot for loading hourly actual values.
"""

from datetime import timedelta, datetime, timezone
import logging
import sys
import os
import tempfile
from requests import Session
from urllib.parse import urljoin
import pandas as pd
from app import configure_logging, config
from app.time_utils import get_pst_now, PST_UTC_OFFSET, get_pst_tz
from app.fireweather_bot import (BC_FIRE_WEATHER_BASE_URL, BC_FIRE_WEATHER_ENDPOINT, _authenticate_session,
                                _get_csv_url, _download_csv, _get_station_names_to_codes)

# If running as it's own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


class HourlyActualsBot():

    def __init__(self):
        self.now = get_pst_now()
        print('now is {}'.format(self.now))

    def get_start_date(self) -> int:
        """ Return time an hour ago. E.g. if it's 17h15 now, we'd get YYYYMMDD16"""
        hour_ago = self.now - timedelta(hours=1)
        return int(hour_ago.strftime('%Y%m%d%H'))

    def get_end_date(self) -> int:
        """ Return now. E.g. if it's 17h15 now, we'd get YYYYMMDD17 """
        return int(self.now.strftime('%Y%m%d%H'))

    def fix_pandas_datetime(self, panda_datetime):
        """ We want to be explicit about timezones, pandas gives us a timezone naive date - this is no
        good! We know the date we get is in PST, and we know we need to store it in UTC.
        """
        # go from pandas to python native:
        python_date = panda_datetime.to_pydatetime()
        # we want to work in utc:
        python_date = python_date.replace(tzinfo=timezone.utc)
        # but alse need to adjust our time, because it's in PST:
        return python_date - timedelta(hours=PST_UTC_OFFSET)

    def process_csv(self, csv_path: str):
        with open(csv_path, 'r') as csv_file:
            data_df = pd.read_csv(csv_file)
        station_codes = _get_station_names_to_codes()
        # replace 'display_name' column (station name) in df with station_id
        # and rename the column appropriately
        data_df['display_name'].replace(station_codes, inplace=True)
        data_df.rename(columns={'display_name': 'station_code'}, inplace=True)
        
        # weather_date is formatted yyyymmddhh as an int - need to reformat it as a Timestamp
        # TODO: make it pst!
        dates = pd.to_datetime(data_df['weather_date'], format='%Y%m%d%H')
        # dates = dates.transform(lambda x: x.tz_localize(tz=get_pst_tz()))
        # dates = dates.tz_localize('UTC')
        data_df['weather_date'] = dates
        # write to database using _session's engine
        # session = app.db.database.get_session()
        # write the data_df to the database one row at a time, so that if data_df contains >=1 rows that are
        # duplicates of what is already in the db, the write won't fail for the unique rows
        # NOTE: iterating over the data_df one Series (row) at a time is ugly, but until pandas is updated
        # with a fix, this is the easiest work-around.
        # See https://github.com/pandas-dev/pandas/issues/15988
        # pylint: disable=unused-variable
        for index, row in data_df.iterrows():
            # try:
            data = row.to_dict()
            data['weather_date'] = self.fix_pandas_datetime(data['weather_date'])

            print('{}'.format(data))
            # session.add(NoonForecasts(**row.to_dict()))
            # session.commit()
            # except IntegrityError:
            #     LOGGER.info('Skipping duplicate record')
            # session.rollback()

    def run(self):
        with Session() as session:
            _authenticate_session(session)
            # Submit the POST request to query hourlies for the station.
            request_body = {
                'Start_Date': self.get_start_date(),
                'End_Date': self.get_end_date(),
                'Format': 'CSV',
                'cboFilters': config.get('BC_FIRE_WEATHER_FILTER_ID'),
                'rdoReport': 'OSBH',
            }
            url = urljoin(BC_FIRE_WEATHER_BASE_URL, BC_FIRE_WEATHER_ENDPOINT)
            response = session.post(url, data=request_body)
            # Extract csv url, and download.
            csv_url = _get_csv_url(response.text)
            with tempfile.TemporaryDirectory() as temp_path:
                filename = _download_csv(session, csv_url, temp_path)
                # Proces the csv
                self.process_csv(filename)
                # Delete the file, now that we're done.
                os.remove(filename)
            
            logger.info('response from session: %s', csv_url)
            # print(response.text)


def main():
    """ Makes the appropriate method calls in order to submit a query to the BC FireWeather Phase 1 API
    to get hourly values for all weather stations, downloads the resulting CSV file, writes
    the CSV file to the database, then deletes the local copy of the CSV file.
    """
    logger.debug('Retrieving hourly actuals...')
    bot = HourlyActualsBot()
    bot.run()
    # Exit with 0 - success.
    sys.exit(0)


if __name__ == '__main__':
    main()
