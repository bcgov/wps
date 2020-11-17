""" Types etc. common to models
"""
import logging
from datetime import datetime
from sqlalchemy import (TIMESTAMP)
from sqlalchemy.types import TypeDecorator


logger = logging.getLogger(__name__)


class TZTimeStamp(TypeDecorator):  # pylint: disable=abstract-method
    """ TimeStamp type that ensures that timezones are always specified.
    If the timezone isn't specified, you aren't guaranteed that you're going to get consistent times. """
    impl = TIMESTAMP(timezone=True)

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime) and value.tzinfo is None:
            logger.warning('type:%s tzinfo:%s', type(value), value.tzinfo)
            raise ValueError('{!r} must be TZ-aware'.format(value))
        return value

    def __repr__(self):
        return 'TZTimeStamp()'
