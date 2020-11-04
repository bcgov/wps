"""
Module to send notifications to team RocketChat channel.
Notification content can be customized based on requestor.
"""

import requests
from app import config


def send_rocketchat_notification(text: str):
    """ Sends message with specified text to configured Rocketchat channel. """
    response = requests.post(
        config.get('ROCKET_URL_POST_MESSAGE'),
        headers={
            'X-Auth-Token': config.get('ROCKET_AUTH_TOKEN'),
            'X-User-Id': config.get('ROCKET_USER_ID'),
            'Content-Type': 'application/json'
        },
        json={
            'channel': config.get('ROCKET_CHANNEL'),
            'text': text
        }
    )
    return response.json()
