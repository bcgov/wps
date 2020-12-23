"""
Module to send notifications to team RocketChat channel.
Notification content can be customized based on requestor.
"""
import traceback
import logging
import requests
from app import config

logger = logging.getLogger(__name__)


def send_rocketchat_notification(text: str, exc_info: Exception) -> dict:
    """ Sends message with specified text to configured Rocketchat channel.

    We don't want this method to raise any exceptions, as we don't want to
    unintentionally break any kind of error management flow. (We only use
    rocket chat notification when something goes wrong).

    If you want to know if this method worked or not, you'll have to inspect
    the response.
    """
    full_message = '{}\n{}: {}\n{}'.format(text,
                                           config.get('HOSTNAME'),
                                           exc_info,
                                           traceback.format_exception(
                                               etype=type(exc_info),
                                               value=exc_info,
                                               tb=exc_info.__traceback__))
    result = None
    try:
        response = requests.post(
            config.get('ROCKET_URL_POST_MESSAGE'),
            headers={
                'X-Auth-Token': config.get('ROCKET_AUTH_TOKEN'),
                'X-User-Id': config.get('ROCKET_USER_ID'),
                'Content-Type': 'application/json'
            },
            json={
                'channel': config.get('ROCKET_CHANNEL'),
                'text': full_message
            }
        )
        result = response.json()
    except Exception as exception:  # pylint: disable=broad-except
        # not doing exc_info=exception - as this causes a lot of noise, and we're more interested
        # in the main code!
        logger.error('failed to send rocket chat notification %s', exception)
    return result
