import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.sfms.date_range_processor import BUIDateRangeProcessor
import app.sfms.date_range_processor

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)


@pytest.mark.asyncio
class TestBUIDateRangeProcessor:
    @pytest.fixture
    def processor(self):
        start_datetime = TEST_DATETIME
        days = 2
        return BUIDateRangeProcessor(start_datetime, days)

    def test_get_previous_fwi_keys_first_day(self, processor):
        # test the _get_previous_fwi_keys method for the first day
        day = 0
        previous_fwi_datetime = TEST_DATETIME - timedelta(days=1)

        dc_key, dmc_key = processor._get_previous_fwi_keys(day, previous_fwi_datetime)

        # Day 0 fwi keys should come from the sfms uploads dir
        assert "uploads" in dc_key
        assert "uploads" in dmc_key

    def test_get_previous_fwi_keys_following_days(self, processor):
        # test the _get_previous_fwi_keys method for the second day
        day = 1
        previous_fwi_datetime = TEST_DATETIME - timedelta(days=1)

        dc_key, dmc_key = processor._get_previous_fwi_keys(day, previous_fwi_datetime)

        # Day 1 fwi keys should come from the calculated s3 dir
        assert "calculated" in dc_key
        assert "calculated" in dmc_key
