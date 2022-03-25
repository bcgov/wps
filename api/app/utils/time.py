""" Functions for dealing with time """
from datetime import datetime, timezone, timedelta, date
from typing import Final


PST_UTC_OFFSET: Final[int] = -8
PDT_UTC_OFFSET: Final[int] = -7


def _get_pst_tz() -> datetime:
    """ Easily mockable Pacific Standard Timezone (PST) : UTC-8 function"""
    return timezone(timedelta(hours=PST_UTC_OFFSET), name="PST")


def get_pst_tz() -> datetime:
    """ Get the Pacific Standard Timezone (PST) : UTC-8"""
    return _get_pst_tz()


def _get_utc_now() -> datetime:
    """ Easily mockable utc function """
    return datetime.now(tz=timezone.utc)


def get_utc_now() -> datetime:
    """ Helper function to get the current UTC time"""
    return _get_utc_now()


def _get_pst_now() -> datetime:
    """ Easily mockable pst function """
    return datetime.now(tz=get_pst_tz())


def get_pst_now() -> datetime:
    """ Helper function to get the current PST time """
    return _get_pst_now()


def get_pst_today_start_and_end():
    """ Get the start and end datetime range for today in PST since app assumes all is in PST."""
    today = datetime.now(tz=get_pst_tz())
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    return start, end


def get_hour_20_from_date(date_of_interest: date) -> datetime:
    """ Helper to return datetime at hour 20 in utc """
    return datetime(year=date_of_interest.year,
                    month=date_of_interest.month,
                    day=date_of_interest.day,
                    hour=20, tzinfo=timezone.utc)


def get_hour_20(time_of_interest: datetime) -> datetime:
    """ Helper to return datetime at hour 20 in utc """
    return datetime(year=time_of_interest.year,
                    month=time_of_interest.month,
                    day=time_of_interest.day,
                    hour=20, tzinfo=timezone.utc)


def convert_utc_to_pdt(time_of_interest: datetime) -> datetime:
    """ Get the datetime in Pacific Daylight Timezone (PDT) : UTC-7 given a
    datetime in UTC timezone """
    return time_of_interest.astimezone(timezone(offset=timedelta(hours=PDT_UTC_OFFSET)))


def get_julian_date_now():
    """ Returns current day of year """
    now_date = get_utc_now()
    return now_date.timetuple().tm_yday


def get_julian_date(time_of_interest: datetime):
    """ Returns Julian day of year for time_of_interest specified in arg. """
    return time_of_interest.timetuple().tm_yday
