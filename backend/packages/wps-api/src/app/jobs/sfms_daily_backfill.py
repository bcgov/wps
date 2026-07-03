"""Run SFMS daily actual jobs over an inclusive date range.

Usage:
    python -m app.jobs.sfms_daily_backfill \
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
from typing import Awaitable, Callable

from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging

from app.jobs.sfms_daily_actuals import run_sfms_daily_actuals

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackfillFailure:
    """One failed date from a backfill run."""

    target_date: date
    error: Exception

    def message(self) -> str:
        """Return a compact failure message for logs and exceptions."""
        return f"{self.target_date.isoformat()}: {self.error}"


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD CLI date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from error


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


async def run_backfill_step(
    target_date: date,
    action: Callable[[], Awaitable[None]],
    failures: list[BackfillFailure],
    continue_on_error: bool,
) -> None:
    """Run one actuals date and optionally continue after a failure."""
    logger.info("Starting SFMS actuals backfill for %s", target_date)
    try:
        await action()
        logger.info("Completed SFMS actuals backfill for %s", target_date)
    except Exception as error:
        logger.exception("SFMS actuals backfill failed for %s", target_date)
        if not continue_on_error:
            raise
        failures.append(BackfillFailure(target_date, error))


async def run_sfms_daily_backfill(
    start_date: date,
    end_date: date,
    continue_on_error: bool = False,
) -> None:
    """Run SFMS daily actuals over an inclusive date range."""
    failures: list[BackfillFailure] = []

    for target_date in iter_dates(start_date, end_date):
        await run_backfill_step(
            target_date,
            lambda target_date=target_date: run_sfms_daily_actuals(
                actual_target_datetime(target_date)
            ),
            failures,
            continue_on_error,
        )

    if failures:
        failure_messages = "; ".join(failure.message() for failure in failures)
        raise RuntimeError(f"SFMS backfill completed with failures: {failure_messages}")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the SFMS daily backfill job."""
    parser = argparse.ArgumentParser(description="Run SFMS daily actuals over a date range.")
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
