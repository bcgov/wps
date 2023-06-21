from datetime import datetime
from app.utils.time import get_model_prune_range, get_utc_datetime, get_days_from_range


def test_get_utc_datetime():
    """ A timezone ambiguous datetime is localized and returned as UTC """
    oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    utc_datetime = get_utc_datetime(oct_1_2022)
    assert (utc_datetime.tzname() == "UTC")
    assert (utc_datetime.hour == 15)


def test_time_range_basic():
    "Basic day range test"
    oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    oct_10_2022 = datetime(year=2022, month=10, day=10, hour=8, minute=30, second=30)

    days = get_days_from_range(oct_1_2022, oct_10_2022)
    assert (len(days) == 10)


def test_time_range_same_day():
    "Number of days between the same day just 1, the same day"
    oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    days = get_days_from_range(oct_1_2022, oct_1_2022)
    assert (len(days) == 1)
    assert (days[0] == oct_1_2022)


def test_time_range_different_times():
    "Number of days between the same day different times is 1, the earlier day+time"
    oct_1_2022_8_30 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    oct_1_2022_9_30 = datetime(year=2022, month=10, day=1, hour=9, minute=30, second=30)
    days = get_days_from_range(oct_1_2022_8_30, oct_1_2022_9_30)
    assert (len(days) == 1)
    assert (days[0] == oct_1_2022_8_30)


def test_time_range_end_before_start():
    "If end date is before start date there are no days between them"
    oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    oct_10_2022 = datetime(year=2022, month=10, day=10, hour=8, minute=30, second=30)
    days = get_days_from_range(oct_10_2022, oct_1_2022)
    assert (len(days) == 0)


def test_model_prune_range_end_before_max_end():
    "If start and end are well before 19 days before now, accept that range"
    now_nov_30_2022 = datetime(year=2022, month=11, day=30, hour=8, minute=30, second=30)
    start_oct_1_2022 = datetime(year=2022, month=10, day=1, hour=8, minute=30, second=30)
    end_oct_14_2022 = datetime(year=2022, month=10, day=14, hour=8, minute=30, second=30)

    range_start, range_end = get_model_prune_range(now_nov_30_2022, start_oct_1_2022, end_oct_14_2022)
    assert start_oct_1_2022 == range_start
    assert end_oct_14_2022 == range_end


def test_model_prune_range_end_empty_if_past_max_end():
    "If start is after max end, "
    now_nov_30_2022 = datetime(year=2022, month=11, day=30, hour=8, minute=30, second=30)
    start_nov_20_2022 = datetime(year=2022, month=11, day=20, hour=8, minute=30, second=30)
    end_dec_4_2022 = datetime(year=2022, month=12, day=4, hour=8, minute=30, second=30)

    range_start, range_end = get_model_prune_range(now_nov_30_2022, start_nov_20_2022, end_dec_4_2022)
    assert range_start is None
    assert range_end is None


def test_model_prune_range_end_clamped_to_max_end():
    "If start is before max end but end is after max end, clamp end to max end"
    now_nov_30_2022 = datetime(year=2022, month=11, day=30, hour=8, minute=30, second=30)
    start_nov_10_2022 = datetime(year=2022, month=11, day=8, hour=8, minute=30, second=30)
    end_nov_24_2022 = datetime(year=2022, month=11, day=22, hour=8, minute=30, second=30)

    expected_clamped_end = datetime(year=2022, month=11, day=9, hour=8, minute=30, second=30)

    range_start, range_end = get_model_prune_range(now_nov_30_2022, start_nov_10_2022, end_nov_24_2022)
    assert range_start == start_nov_10_2022
    assert range_end == expected_clamped_end
