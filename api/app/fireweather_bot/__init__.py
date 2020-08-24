""" Code common to fireweather bots
"""
import logging
import re
from requests import Session
from requests_ntlm import HttpNtlmAuth
from app import config


BC_FIRE_WEATHER_BASE_URL = 'https://bcfireweatherp1.nrs.gov.bc.ca'
BC_FIRE_WEATHER_ENDPOINT = 'Scripts/Public/Common/Results_Report.asp'


logger = logging.getLogger(__name__)


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
