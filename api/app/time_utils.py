"""
"""
from datetime import datetime, timezone, timedelta
from typing import Final


PST_UTC_OFFSET: Final[int] = -8


def get_utc_now():
    """ Helper function to get the current UTC time (easy function to mock out in testing) """
    return datetime.now(tz=timezone.utc)


def get_pst_now():
    """ Helper function to get the current PST time (easy function to mock out in testing) """
    return datetime.now(tz=timezone(timedelta(hours=PST_UTC_OFFSET), name="PST"))
