""" This is a bot to pull hourly weather actuals from the BC FireWeather Phase 1 API
for each weather station and store the results (from a CSV file) in our database.
"""
import os
import json
import sys
import logging
import logging.config
import tempfile
from datetime import timedelta
import re
from typing import List, Dict
from abc import abstractmethod, ABC
from requests import Session
from requests.compat import urljoin
from requests_ntlm import HttpNtlmAuth
from sqlalchemy.exc import IntegrityError
import pandas as pd
from app import config
import app.db.database
from app.db.models import NoonForecasts
from app.wildfire_one import _get_now, _get_stations_local


# If running as it's own process, configure loggin appropriately.
if __name__ == "__main__":
    LOGGING_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.json')
    if os.path.exists(LOGGING_CONFIG):
        with open(LOGGING_CONFIG) as config_file:
            CONFIG = json.load(config_file)
        logging.config.dictConfig(CONFIG)

LOGGER = logging.getLogger(__name__)

TEMP_CSV_FILENAME = 'weather_station_forecasts.csv'
BC_FIRE_WEATHER_BASE_URL = 'https://bcfireweatherp1.nrs.gov.bc.ca'

dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'data/weather_stations.json')


# pylint: disable=too-few-public-methods, broad-except, no-member
class BuildQuery(ABC):
    """ Base class for building query urls and params """

    def __init__(self):
        """ Initialize object """
        self.base_url = BC_FIRE_WEATHER_BASE_URL

    @abstractmethod
    def query(self) -> [str, dict]:
        """ Return query url and params """

# pylint: disable=too-few-public-methods


class BuildQueryByStationCode(BuildQuery):
    """ Class for building a url and params to request a list of stations by code """

    def __init__(self, station_codes: List[int]):
        """ Initialize object """
        super().__init__()
        self.querystring = ''
        for code in station_codes:
            if len(self.querystring) > 0:
                self.querystring += ' or '
            self.querystring += 'stationCode=={}'.format(code)

    def query(self) -> [str, dict]:
        """ Return query url and params for a list of stations """
        params = {'query': self.querystring}
        url = urljoin(
            self.base_url, 'Scripts/Public/Common/Results_Report.asp')
        return [url, params]


def _authenticate_session(session: Session) -> Session:
    """ Authenticate the session using NTLM auth
    """
    password = config.get('BC_FIRE_WEATHER_SECRET')
    user = config.get('BC_FIRE_WEATHER_USER')
    LOGGER.info('Authenticating user %s at %s', user, BC_FIRE_WEATHER_BASE_URL)
    response = session.get(BC_FIRE_WEATHER_BASE_URL,
                           auth=HttpNtlmAuth('idir\\'+user, password))

    if re.search(r"server error", response.text, re.IGNORECASE):
        raise Exception(
            "Server Error occurred while authenticating user. \n {}".format(response.text))
    else:
        return session


def prepare_fetch_noon_forecasts_query():
    """ Prepare url and params to fetch forecast noon-time values from the BC FireWeather Phase 1 API.
    """
    start_date = _get_start_date()
    end_date = _get_end_date()
    LOGGER.debug('requesting noon forecasts from %s to %s',
                 start_date, end_date)
    # Prepare query params and query:
    request_body = {
        'Start_Date': int(start_date),
        'End_Date': int(end_date),
        'Format': 'CSV',
        'cboFilters': config.get('BC_FIRE_WEATHER_FILTER_ID'),
        'rdoReport': 'OSBD',
    }
    endpoint = ('Scripts/Public/Common/Results_Report.asp')
    url = urljoin(BC_FIRE_WEATHER_BASE_URL, endpoint)
    return url, request_body


def fetch_noon_forecasts(
        session: Session):
    """ Fetch daily weather forecasts (noon values) for a given station.
    """
    url, request_body = prepare_fetch_noon_forecasts_query()
    # Get forecasts
    resp = session.post(url, data=request_body)
    search_result = re.search(r"fire_weather\/csv\/.+\.csv", resp.text)
    if search_result:
        LOGGER.info('Fetching CSV from %s', search_result.group(0))
        return search_result.group(0)
    else:
        raise Exception("Couldn't find the csv url.")


def get_csv(
        session: Session,
        csv_url: str,
        temp_path: str):
    """ Fetch CSV of hourly actual weather for a station.
    """
    url = urljoin(BC_FIRE_WEATHER_BASE_URL, csv_url)
    response = session.get(
        url,
        auth=HttpNtlmAuth('idir\\'+config.get('BC_FIRE_WEATHER_USER'),
                          config.get('BC_FIRE_WEATHER_SECRET'))
    )
    content = response.content

    # Need to write response content to a CSV file - once the CSV file has been read, it will be deleted
    with open(os.path.join(temp_path, TEMP_CSV_FILENAME), 'wb') as csv_file:
        csv_file.write(content)


def get_noon_forecasts(temp_path: str):
    """ Send POST request to BC FireWeather API to generate a CSV,
    then send GET request to retrieve the CSV,
    then parse the CSV and store in DB.
    """
    with Session() as session:
        _authenticate_session(session)
        # Submit the POST request to query forecasts for the station
        csv_url = fetch_noon_forecasts(session)
        # Use the returned URL to fetch the CSV data for the station
        get_csv(session, csv_url, temp_path)
        # Parse the CSV data
        parse_csv(temp_path)
        LOGGER.debug('Finished writing noon forecasts to database')


def parse_csv(temp_path: str):
    """ Given a CSV of forecast noon-time weather data for a station, load the CSV into a
    pandas dataframe, then insert the dataframe into the DB. (This 2-step process is
    the neatest way to write CSVs into a DB.)
    """
    with open(os.path.join(temp_path, TEMP_CSV_FILENAME), 'r') as csv_file:
        data_df = pd.read_csv(csv_file)
    station_codes = _get_station_names_to_codes()
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
    # delete the temp CSV file - it's not needed anymore
    os.remove(os.path.join(temp_path, TEMP_CSV_FILENAME))
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
            session.add(NoonForecasts(**row.to_dict()))
            session.commit()
        except IntegrityError:
            LOGGER.info('Skipping duplicate record')
            session.rollback()


def _get_start_date():
    """ Helper function to get the start date for query (if morning run, use current day; if evening run,
    use tomorrow's date, since we only want forecasts, not actuals)
    Strip out time, we just want yyyymmdd """
    date = ''
    now = _get_now()    # returns time in UTC
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
    five_days_ahead = _get_now() + timedelta(days=5)
    return five_days_ahead.strftime('%Y%m%d')


def _get_station_names_to_codes() -> Dict:
    """ Helper function to create dictionary of (station_name: station_code) key-value pairs
    Is used when replacing station names with station IDs in dataframe
    """
    station_data = _get_stations_local()
    station_codes = {
        station['name']: station['code'] for station in station_data
    }
    # have to hack this, because BC FireWeather API spells a certain station 'DARCY'
    # while our weather_stations.json spells the station 'D'ARCY'
    station_codes['DARCY'] = station_codes.pop('D\'ARCY')
    return station_codes

# pylint: disable=invalid-name


def main():
    """ Makes the appropriate method calls in order to submit a query to the BC FireWeather Phase 1 API
    to get (up to) 5-day forecasts for all weather stations, downloads the resulting CSV file, writes
    the CSV file to the database, then deletes the local copy of the CSV file.
    """
    LOGGER.debug('Retrieving noon forecasts...')
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            get_noon_forecasts(temp_path)
        LOGGER.debug(
            'Finished retrieving noon forecasts for all weather stations.')
        # Exit with 0 - success.
        sys.exit(0)
    except IntegrityError as exception:
        LOGGER.error(
            "One or more records were not written to the database because they are duplicates.",
            exc_info=exception)
        # Exit non 0 - failure.
        sys.exit(1)
    except Exception as exception:
        # Exit non 0 - failure.
        LOGGER.error('Failed to retrieve noon forecasts.',
                     exc_info=exception)
        sys.exit(1)


if __name__ == '__main__':
    main()
