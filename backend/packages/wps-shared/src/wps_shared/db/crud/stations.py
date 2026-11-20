""" Methods relating to reading station data from database.
"""
from datetime import datetime, timedelta, timezone
from wps_shared.utils.time import get_hour_20


def get_noon_date(date_of_interest: datetime) -> datetime:
    """
    If before noon today, give noon from day before.
    If after noon today, give noon from date of interest.
    """
    noon_for_date_of_interest = get_hour_20(date_of_interest)
    if date_of_interest < noon_for_date_of_interest:
        # Get noon from the day before the date of intereset.
        day_before = date_of_interest - timedelta(days=1)
        return datetime(
            year=day_before.year, month=day_before.month, day=day_before.day, hour=20, tzinfo=timezone.utc)
    # Get noon for the date of intereset.
    return noon_for_date_of_interest
