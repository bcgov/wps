""" Code common to fireweather bots
"""
import logging
import re
import os
from urllib.parse import urljoin
from pathlib import PurePath
from requests import Session
from requests_ntlm import HttpNtlmAuth
from app import config
from app.wildfire_one import _get_stations_local


BC_FIRE_WEATHER_BASE_URL = 'https://bcfireweatherp1.nrs.gov.bc.ca'
BC_FIRE_WEATHER_ENDPOINT = 'Scripts/Public/Common/Results_Report.asp'


logger = logging.getLogger(__name__)


class CSVNotFoundException(Exception):
    pass


def _authenticate_session(session: Session) -> Session:
    """ Authenticate the session using NTLM auth
    """
    password = config.get('BC_FIRE_WEATHER_SECRET')
    user = config.get('BC_FIRE_WEATHER_USER')
    logger.info('Authenticating user %s at %s', user, BC_FIRE_WEATHER_BASE_URL)
    resp = session.get(BC_FIRE_WEATHER_BASE_URL,
                       auth=HttpNtlmAuth('idir\\'+user, password))

    if resp and re.search(r"server error", resp.text, re.IGNORECASE):
        raise Exception(
            "Server Error occurred while authenticating user. \n {}".format(resp.text))

    return session


def _get_csv_url(content: str):
    search_result = re.search(r"fire_weather\/csv\/.+\.csv", content)
    if not search_result:
        raise CSVNotFoundException("Couldn't find the csv url.")
    logger.info('CSV file identified as %s', search_result.group(0))
    file_path = search_result.group(0)
    return urljoin(BC_FIRE_WEATHER_BASE_URL, file_path)


def _get_csv_response(session: Session, url: str):
    return session.get(
        url,
        auth=HttpNtlmAuth('idir\\'+config.get('BC_FIRE_WEATHER_USER'),
                          config.get('BC_FIRE_WEATHER_SECRET'))
    )


def _get_station_names_to_codes() -> dict:
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


def _download_csv(
        session: Session,
        url: str,
        target_path: str) -> str:
    """ Fetch CSV of hourly actual weather for a station.
    """
    response = _get_csv_response(session, url)

    csv_filename = PurePath(url).name
    target_filename = os.path.join(target_path, csv_filename)
    
    # Need to write response content to a CSV file - once the CSV file has been read, it will be deleted
    with open(target_filename, 'wb') as csv_file:
        csv_file.write(response.content)
    return target_filename
