from datetime import datetime, timezone

import pytest

from app.routers.fba import get_advisory_valid_until


def test_get_advisory_valid_until_before_cutoff():
    run_datetime = datetime(2025, 8, 27, 0, 29, tzinfo=timezone.utc)

    assert get_advisory_valid_until(run_datetime) == datetime(2025, 8, 27, 1, tzinfo=timezone.utc)


def test_get_advisory_valid_until_at_cutoff():
    run_datetime = datetime(2025, 8, 27, 0, 30, tzinfo=timezone.utc)

    assert get_advisory_valid_until(run_datetime) == datetime(2025, 8, 27, 15, tzinfo=timezone.utc)


def test_get_advisory_valid_until_after_cutoff():
    run_datetime = datetime(2025, 8, 27, 0, 31, tzinfo=timezone.utc)

    assert get_advisory_valid_until(run_datetime) == datetime(2025, 8, 27, 15, tzinfo=timezone.utc)


def test_get_advisory_valid_until_without_timezone():
    run_datetime = datetime(2025, 8, 26, 17, 29)

    with pytest.raises(ValueError, match=f"{run_datetime} must be timezone-aware."):
        get_advisory_valid_until(run_datetime)
