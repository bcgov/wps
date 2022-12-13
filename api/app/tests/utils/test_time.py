from datetime import datetime
from app.utils.time import get_utc_datetime


def test_get_utc_datetime():
    """ A timezone ambiguous datetime is localized and returned as UTC """
    oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    utc_datetime = get_utc_datetime(oct_1_2022)
    assert (utc_datetime.tzname() == "UTC")
    assert (utc_datetime.hour == 15)
