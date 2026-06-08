"""
Module to send chatops notifications.
Notification content can be customized based on requestor.
"""

import logging
import threading
import traceback
from datetime import datetime, timezone

import requests

from wps_shared import config

logger = logging.getLogger(__name__)

webhook_max_char_len = 2000


def send_chatops_notification(text: str, exc_info: Exception) -> str | None:
    """Sends message with specified text to configured chatops webhook.

    We don't want this method to raise any exceptions, as we don't want to
    unintentionally break any kind of error management flow. (We only use
    a chatops notification when something goes wrong).

    If you want to know if this method worked or not, you'll have to inspect
    the response.
    """
    traceback_str = "".join(
        traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
    )
    header = (
        f"{datetime.now(tz=timezone.utc).isoformat()}\n"
        f"{text}\n"
        f"{config.get('HOSTNAME')} ({threading.get_native_id()}): {exc_info}\n"
    )
    max_tb_len = webhook_max_char_len - len(header) - 8  # 8 for "```\n" + "\n```"
    full_message = f"{header}```\n{traceback_str[:max_tb_len]}\n```"
    pod_logs_url = f"{config.get('OPENSHIFT_CONSOLE_URL')}/k8s/ns/{config.get('PROJECT_NAMESPACE')}/pods/{config.get('HOSTNAME')}/logs"
    result = None
    try:
        response = requests.post(
            config.get("CHATOPS_URL"),
            headers={
                "token": f"{config.get('CHATOPS_AUTH_TOKEN')}",
                "Content-Type": "application/json",
            },
            json={
                "title": config.get("HOSTNAME"),
                "severity": "critical",
                "body": full_message,
                "url": pod_logs_url,
                "urlLabel": "View Logs",
            },
            timeout=10,
        )
        logger.info("chatops webhook response: %s %s", response.status_code, response.text)
        result = response.json()
    except Exception as exception:
        # not doing exc_info=exception - as this causes a lot of noise, and we're more interested
        # in the main code!
        logger.error("failed to send chatops notification %s", exception)
    return result
