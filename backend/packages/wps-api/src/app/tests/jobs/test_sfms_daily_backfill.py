"""Unit tests for SFMS daily date-range backfill."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.jobs.sfms_daily_backfill import (
    BackfillRunType,
    actual_target_datetime,
    forecast_run_datetime,
    iter_dates,
    run_sfms_daily_backfill,
)

MODULE_PATH = "app.jobs.sfms_daily_backfill"


def test_iter_dates_includes_start_and_end_dates():
    result = list(iter_dates(date(2026, 6, 25), date(2026, 6, 27)))

    assert result == [date(2026, 6, 25), date(2026, 6, 26), date(2026, 6, 27)]


def test_iter_dates_rejects_end_date_before_start_date():
    with pytest.raises(ValueError, match="end date"):
        list(iter_dates(date(2026, 6, 27), date(2026, 6, 25)))


def test_actual_target_datetime_uses_midnight_utc():
    result = actual_target_datetime(date(2026, 6, 25))

    assert result == datetime(2026, 6, 25, tzinfo=timezone.utc)


def test_forecast_run_datetime_uses_after_actuals_available_time():
    result = forecast_run_datetime(date(2026, 6, 25))

    assert result == datetime(2026, 6, 25, 23, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_run_sfms_daily_backfill_runs_actuals_for_each_date(mocker: MockerFixture):
    mock_actuals = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_actuals", new_callable=AsyncMock)
    mock_forecasts = mocker.patch(f"{MODULE_PATH}.run_sfms_daily_forecasts", new_callable=AsyncMock)

    await run_sfms_daily_backfill(date(2026, 6, 25), date(2026, 6, 26), BackfillRunType.ACTUAL)

    assert [call.args[0] for call in mock_actuals.call_args_list] == [
        datetime(2026, 6, 25, tzinfo=timezone.utc),
        datetime(2026, 6, 26, tzinfo=timezone.utc),
    ]
    mock_forecasts.assert_not_awaited()


@pytest.mark.anyio
async def test_run_sfms_daily_backfill_runs_both_in_date_order(mocker: MockerFixture):
    calls = []

    async def run_actual(target_datetime: datetime):
        calls.append(("actual", target_datetime))

    async def run_forecast(run_datetime: datetime):
        calls.append(("forecast", run_datetime))

    mocker.patch(f"{MODULE_PATH}.run_sfms_daily_actuals", side_effect=run_actual)
    mocker.patch(f"{MODULE_PATH}.run_sfms_daily_forecasts", side_effect=run_forecast)

    await run_sfms_daily_backfill(date(2026, 6, 25), date(2026, 6, 26), BackfillRunType.BOTH)

    assert calls == [
        ("actual", datetime(2026, 6, 25, tzinfo=timezone.utc)),
        ("forecast", datetime(2026, 6, 25, 23, tzinfo=timezone.utc)),
        ("actual", datetime(2026, 6, 26, tzinfo=timezone.utc)),
        ("forecast", datetime(2026, 6, 26, 23, tzinfo=timezone.utc)),
    ]


@pytest.mark.anyio
async def test_run_sfms_daily_backfill_can_continue_after_error(mocker: MockerFixture):
    mock_actuals = mocker.patch(
        f"{MODULE_PATH}.run_sfms_daily_actuals",
        new_callable=AsyncMock,
        side_effect=[RuntimeError("first failed"), None],
    )

    with pytest.raises(RuntimeError, match="completed with failures"):
        await run_sfms_daily_backfill(
            date(2026, 6, 25),
            date(2026, 6, 26),
            BackfillRunType.ACTUAL,
            continue_on_error=True,
        )

    assert mock_actuals.await_count == 2
