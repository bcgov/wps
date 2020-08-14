""" Configuration related code
"""
import logging
from decouple import config

LOGGER = logging.getLogger(__name__)


def get(key, default=None):
    """ Use decouple.config to retreive values, logging a warning if the value is not found.

    - Using decouple.config in only one module, makes it easier to stub out calls to os.getenv. (No need to
        stub it out per module, can just stub it once.)
    - Using this function ensure that we retrieve environment variables in a consistent manner. (E.g. like
        logging a warning if the variable isn't found, and ability to switch out config libraries.)
    """
    value = config(key, default)
    if value is None:
        LOGGER.warning('Expected environment variable (%s) not set.', key)
    return value
