"""Shared success/failure handling for the weather model download jobs.

Every model job (Env Canada, NOAA) does the same two things once its downloads are done:
judge the run from its counters, then act on that verdict. Both halves live here so the
jobs can't drift apart on what counts as a failure.

The contract:

    NoFilesProcessed            an upstream outage - warn to chatops, exit EX_OK. The next
                                scheduled run picks up whatever we missed.
    CompletedWithSomeExceptions something we can act on - exit EX_SOFTWARE.
    (no exception)              success - exit EX_OK.

A real exception always beats an outage: NoFilesProcessed is excused as "the retries will
get it", so it must never be raised for a run that also hit genuine exceptions.
"""

import logging
import os
import sys
from typing import Callable, Protocol

from weather_model_jobs.common_model_fetchers import apply_data_retention_policy
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.weather_models import CompletedWithSomeExceptions, NoFilesProcessed

logger = logging.getLogger(__name__)


class ModelJob(Protocol):
    """What judge_run needs to know about a finished job."""

    files_processed: int
    connection_error_count: int
    exception_count: int


def judge_run(job: ModelJob, source: str, model: str) -> int:
    """Judge a finished run, raising if it didn't go well. Returns the files processed.

    Raises
    ------
    NoFilesProcessed
        Connection failures wiped out the run and nothing else went wrong: an outage.
    CompletedWithSomeExceptions
        At least one URL failed for a reason that isn't an outage.
    """
    if job.connection_error_count > 0:
        logger.warning(
            "%d connection error(s) during run (hourly retries will catch missed files)",
            job.connection_error_count,
        )

    # Only an outage if nothing else went wrong. A real exception in the mix means the job
    # failed for a reason we can act on, and must not be excused as an upstream outage.
    if job.files_processed == 0 and job.connection_error_count > 0 and job.exception_count == 0:
        raise NoFilesProcessed(f"no files processed for {model} — possible outage at {source}")

    if job.exception_count > 0:
        raise CompletedWithSomeExceptions()

    return job.files_processed


def run_model_job(process_models: Callable[[], int], source: str, model: str):
    """Run a model job to completion and exit the process with the appropriate code."""
    try:
        process_models()
        apply_data_retention_policy()
    except NoFilesProcessed as exc:
        # An outage upstream isn't something we can act on, and the hourly retries pick up
        # whatever we missed. Notify at warning severity and exit cleanly so it doesn't
        # surface as a failed job.
        logger.warning("%s", exc)
        rc_message = (
            f":warning: No files processed for {model} model data from {source} "
            "— hourly retries will attempt recovery"
        )
        send_chatops_notification(rc_message, exc, severity="warning")
        sys.exit(os.EX_OK)
    except CompletedWithSomeExceptions:
        logger.warning("completed processing with some exceptions")
        sys.exit(os.EX_SOFTWARE)
    except Exception as exception:
        # We catch and log any exceptions we may have missed.
        logger.exception("unexpected exception processing")
        rc_message = f":poop: Encountered error retrieving {model} model data from {source}"
        send_chatops_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)
