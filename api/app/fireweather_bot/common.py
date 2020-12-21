""" Code common to fireweather bots
"""
from abc import ABC, abstractmethod
import logging
import re
import os
from tempfile import TemporaryDirectory
from urllib.parse import urljoin
from pathlib import PurePath
from requests import Session, HTTPError
from requests_ntlm import HttpNtlmAuth
from app import config
from app.stations import get_stations_synchronously


BC_FIRE_WEATHER_BASE_URL = 'https://bcfireweatherp1.nrs.gov.bc.ca'
BC_FIRE_WEATHER_ENDPOINT = 'Scripts/Public/Common/Results_Report.asp'


logger = logging.getLogger(__name__)


class CSVNotFoundException(Exception):
    """ Exception thrown if CSV is not found """


class AuthenticationException(Exception):
    """ Exception thrown if there's any issue authenticating """


def _authenticate_session(session: Session) -> Session:
    """ Authenticate the session using NTLM auth
    """
    password = config.get('BC_FIRE_WEATHER_SECRET')
    user = config.get('BC_FIRE_WEATHER_USER')
    logger.info('Authenticating user %s at %s', user, BC_FIRE_WEATHER_BASE_URL)
    resp = session.get(BC_FIRE_WEATHER_BASE_URL,
                       auth=HttpNtlmAuth('idir\\'+user, password))

    if resp and re.search(r"server error", resp.text, re.IGNORECASE):
        raise AuthenticationException(
            "Server Error occurred while authenticating user. \n {}".format(resp.text))

    return session


def _infer_csv_url(content: str):
    """ Infer the CSV url from the request response and the base url """
    search_result = re.search(r"fire_weather\/csv\/.+\.csv", content)
    if not search_result:
        raise CSVNotFoundException("Couldn't find the csv url.")
    logger.info('CSV file identified as %s', search_result.group(0))
    file_path = search_result.group(0)
    return urljoin(BC_FIRE_WEATHER_BASE_URL, file_path)


def _request_csv_url(session: Session, request_body: dict):
    """ Submit the POST request to query hourlies for the station, and infer
    the url of the CSV from the response.
    """
    # Construct the url.
    url = urljoin(BC_FIRE_WEATHER_BASE_URL, BC_FIRE_WEATHER_ENDPOINT)
    # Do the post.
    response = session.post(url, data=request_body)
    if response.status_code != 200:
        # Raise an exception if we don't get a 200 response.
        error_message = 'Received status code: {} (expecting 200)'.format(response.status_code)
        raise HTTPError(error_message, response=response)
    # Extract csv url.
    return _infer_csv_url(response.text)


def _get_csv_response(session: Session, url: str):
    return session.get(
        url,
        auth=HttpNtlmAuth('idir\\'+config.get('BC_FIRE_WEATHER_USER'),
                          config.get('BC_FIRE_WEATHER_SECRET'))
    )


def get_station_names_to_codes() -> dict:
    """ Helper function to create dictionary of (station_name: station_code) key-value pairs
    Is used when replacing station names with station IDs in dataframe
    """
    stations = get_stations_synchronously()
    station_codes = {
        station.name: station.code for station in stations
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


class BaseBot(ABC):
    """ Base class for the fire weather bots. The hourly and noon bots are essentially identical, except
    for what the request looks like, and how to process the data. """

    @abstractmethod
    def construct_request_body(self):
        """ Code for constructing the request body that is used to request a CSV from the phase one website
        """
        raise NotImplementedError()

    @abstractmethod
    def process_csv(self, filename: str):
        """ Code for processing the CSV returned from the phase one website and insert it into a databas
        """
        raise NotImplementedError()

    def run(self):
        """ Entry point for running the bot """
        with Session() as session:
            # Authenticate with idir.
            _authenticate_session(session)
            # Build the request body.
            request_body = self.construct_request_body()
            # Get the CSV url.
            csv_url = _request_csv_url(session, request_body)
            with TemporaryDirectory() as temp_path:
                # Download csv into a temporary folder.
                filename = _download_csv(session, csv_url, temp_path)
                # Proces the csv.
                self.process_csv(filename)
                # Delete the file, now that we're done.
                os.remove(filename)
            logger.info('response from session: %s', csv_url)
