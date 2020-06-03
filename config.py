""" Configuration related code
"""
from os import getenv
import logging

LOGGER = logging.getLogger(__name__)


def get(key, default=None):
    """ Use os.getenv to retreive values, logging a warning if the value is not found.

    - Using os.getenv in only one module, makes it easier to stub out calls to os.getenv. (No need to
        stub it out per module, can just stub it once.)
    - Using this function ensure that we retrieve environment variables in a consistent manner. (E.g. like
        logging a warning if the variable isn't found.)
    """
    value = getenv(key, default)
    if value is None:
        LOGGER.warning('Expected environment variable (%s) not set.', key)
    return value
