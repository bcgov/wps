"""Run SFMS daily actual and forecast jobs over an inclusive date range.

Usage:
    python -m app.jobs.sfms_daily_backfill \
        --run-type actual \
        --start-date 2026-06-25 \
        --end-date 2026-06-27

    python -m app.jobs.sfms_daily_backfill \
        --run-type both \
        --start-date 2026-06-25 \
        --end-date 2026-06-27
"""

import argparse
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Awaitable, Callable

from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging

from app.jobs.sfms_daily_actuals import run_sfms_daily_actuals
from app.jobs.sfms_daily_forecasts import run_sfms_daily_forecasts

logger = logging.getLogger(__name__)


class BackfillRunType(StrEnum):
    """SFMS daily job types supported by the backfill."""

    ACTUAL = "actual"
    FORECAST = "forecast"
    BOTH = "both"


@dataclass(frozen=True)
class BackfillFailure:
    """One failed date/job pair from a backfill run."""

    run_type: BackfillRunType
    target_date: date
    error: Exception

    def message(self) -> str:
        """Return a compact failure message for logs and exceptions."""
        return f"{self.run_type.value} {self.target_date.isoformat()}: {self.error}"


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD CLI date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from error


def parse_run_type(value: str) -> BackfillRunType:
    """Parse a run type, accepting singular and plural names."""
    aliases = {
        "actual": BackfillRunType.ACTUAL,
        "actuals": BackfillRunType.ACTUAL,
        "forecast": BackfillRunType.FORECAST,
        "forecasts": BackfillRunType.FORECAST,
        "both": BackfillRunType.BOTH,
    }
    try:
        return aliases[value.lower()]
    except KeyError as error:
        raise argparse.ArgumentTypeError("run type must be actual, forecast, or both") from error


def iter_dates(start_date: date, end_date: date):
    """Yield every date in an inclusive date range."""
    if end_date < start_date:
        raise ValueError("end date must be on or after start date")

    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def actual_target_datetime(target_date: date) -> datetime:
    """Return the datetime shape expected by the daily actuals job."""
    return datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)


def forecast_run_datetime(seed_actual_date: date) -> datetime:
    """Return a run datetime that makes forecasts seed from the requested actual date."""
    return datetime(
        seed_actual_date.year,
        seed_actual_date.month,
        seed_actual_date.day,
        hour=23,
        tzinfo=timezone.utc,
    )


async def run_backfill_step(
    run_type: BackfillRunType,
    target_date: date,
    action: Callable[[], Awaitable[None]],
    failures: list[BackfillFailure],
    continue_on_error: bool,
) -> None:
    """Run one date/job pair and optionally continue after a failure."""
    logger.info("Starting SFMS %s backfill for %s", run_type.value, target_date)
    try:
        await action()
        logger.info("Completed SFMS %s backfill for %s", run_type.value, target_date)
    except Exception as error:
        logger.exception("SFMS %s backfill failed for %s", run_type.value, target_date)
        if not continue_on_error:
            raise
        failures.append(BackfillFailure(run_type, target_date, error))


async def run_sfms_daily_backfill(
    start_date: date,
    end_date: date,
    run_type: BackfillRunType,
    continue_on_error: bool = False,
) -> None:
    """Run SFMS daily jobs over an inclusive date range."""
    failures: list[BackfillFailure] = []

    for target_date in iter_dates(start_date, end_date):
        if run_type in (BackfillRunType.ACTUAL, BackfillRunType.BOTH):
            await run_backfill_step(
                BackfillRunType.ACTUAL,
                target_date,
                lambda target_date=target_date: run_sfms_daily_actuals(
                    actual_target_datetime(target_date)
                ),
                failures,
                continue_on_error,
            )

        if run_type in (BackfillRunType.FORECAST, BackfillRunType.BOTH):
            await run_backfill_step(
                BackfillRunType.FORECAST,
                target_date,
                lambda target_date=target_date: run_sfms_daily_forecasts(
                    forecast_run_datetime(target_date)
                ),
                failures,
                continue_on_error,
            )

    if failures:
        failure_messages = "; ".join(failure.message() for failure in failures)
        raise RuntimeError(f"SFMS backfill completed with failures: {failure_messages}")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the SFMS daily backfill job."""
    parser = argparse.ArgumentParser(description="Run SFMS daily jobs over a date range.")
    parser.add_argument("--run-type", type=parse_run_type, required=True)
    parser.add_argument("--start-date", type=parse_date, required=True)
    parser.add_argument("--end-date", type=parse_date, required=True)
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Attempt the remaining dates after a date fails, then fail the job at the end.",
    )
    return parser


def main() -> None:
    """Main entry point for the backfill job."""
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        asyncio.run(
            run_sfms_daily_backfill(
                args.start_date,
                args.end_date,
                args.run_type,
                continue_on_error=args.continue_on_error,
            )
        )
    except Exception as exception:
        logger.exception("An exception occurred while running SFMS daily backfill")
        send_chatops_notification("Encountered error running SFMS daily backfill", exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
