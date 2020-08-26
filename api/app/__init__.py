""" Root level package
"""
import os
import json
import logging
import logging.config
# database is used externally by alembic.
from . import db  # noqa: F401


def configure_logging():
    """ Configure the logger """
    logging_config = os.path.join(os.path.dirname(__file__), 'logging.json')
    if os.path.exists(logging_config):
        with open(logging_config) as config_file:
            config = json.load(config_file)
        logging.config.dictConfig(config)


def url_join(parts):
    """ Take various parts of a url and join them """
    return "/".join(map(lambda part: part.strip('/'), parts))
