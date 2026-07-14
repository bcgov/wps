"""Unit tests for weather_model_jobs/model_job_runner.py

This is where the weather model jobs decide success from failure. Both Env Canada and NOAA
delegate to judge_run() and run_model_job(), so the rules are pinned here once.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest
from weather_model_jobs import model_job_runner
from weather_model_jobs.model_job_runner import judge_run, run_model_job
from wps_shared.weather_models import CompletedWithSomeExceptions, NoFilesProcessed

SOURCE = "Env Canada"
MODEL = "GDPS"


class FakeJob:
    """A finished job, as judge_run() sees it."""

    def __init__(self, files_processed, connection_error_count, exception_count):
        self.files_processed = files_processed
        self.connection_error_count = connection_error_count
        self.exception_count = exception_count


# How a finished run is judged, over every combination of the three counters it is judged on.
#
# NoFilesProcessed            -> warning to chatops, exits EX_OK (an upstream outage).
# CompletedWithSomeExceptions -> exits EX_SOFTWARE (something we can act on).
# None                        -> no raise, exits EX_OK (success, or nothing new to do).
#
# The rule the corner cases turn on: a real exception always beats an outage, because
# NoFilesProcessed is excused as "the retries will get it" and a genuine bug must not be.
EXIT_DECISION_CASES = [
    # files_processed, connection_errors, exceptions, expected
    (10, 0, 0, None),  # clean run
    (0, 0, 0, None),  # nothing new to do: everything already processed, or not published yet
    (10, 5, 0, None),  # partial outage, but we still got files: retries pick up the rest
    (0, 5, 0, NoFilesProcessed),  # total outage, nothing else wrong
    (0, 5, 3, CompletedWithSomeExceptions),  # outage AND a real bug: the bug wins
    (0, 0, 3, CompletedWithSomeExceptions),  # nothing processed, purely our own fault
    (10, 0, 3, CompletedWithSomeExceptions),  # partial success with real exceptions
    (10, 5, 3, CompletedWithSomeExceptions),  # everything at once: still a real failure
]


def exit_decision_id(case) -> str:
    files_processed, connection_errors, exceptions, expected = case
    outcome = expected.__name__ if expected else "ok"
    return f"{files_processed}processed-{connection_errors}conn-{exceptions}exc-{outcome}"


@pytest.mark.parametrize("case", EXIT_DECISION_CASES, ids=exit_decision_id)
def test_judge_run(case):
    """Pin how a finished run is judged, for every counter combination."""
    files_processed, connection_errors, exceptions, expected = case
    job = FakeJob(files_processed, connection_errors, exceptions)

    if expected is None:
        assert judge_run(job, source=SOURCE, model=MODEL) == files_processed
    else:
        with pytest.raises(expected):
            judge_run(job, source=SOURCE, model=MODEL)


# What run_model_job() does about each verdict judge_run() can reach.
#
# raised_by_process_models, exit_code, chatops_severity (None = no notification at all)
MAIN_OUTCOME_CASES = [
    # A clean run: succeed quietly.
    (None, os.EX_OK, None),
    # An upstream outage: tell us, but don't fail the job - the hourly retries recover it.
    (NoFilesProcessed("no files processed"), os.EX_OK, "warning"),
    # Real exceptions on some URLs: fail the job. Deliberately no chatops (pre-existing).
    (CompletedWithSomeExceptions(), os.EX_SOFTWARE, None),
    # Anything we didn't see coming: fail loudly.
    (ValueError("boom"), os.EX_SOFTWARE, "critical"),
]


def main_outcome_id(case) -> str:
    raised, _, severity = case
    return f"{type(raised).__name__ if raised else 'success'}-{severity or 'no_chatops'}"


@pytest.mark.parametrize("case", MAIN_OUTCOME_CASES, ids=main_outcome_id)
def test_run_model_job(case, mocker, monkeypatch):
    """Pin the exit code and chatops severity produced for every verdict."""
    raised, exit_code, severity = case

    monkeypatch.setattr(model_job_runner, "apply_data_retention_policy", MagicMock())
    chatops_spy = mocker.patch.object(model_job_runner, "send_chatops_notification")

    def process_models():
        if raised is not None:
            raise raised

    with pytest.raises(SystemExit) as excinfo:
        run_model_job(process_models, source=SOURCE, model=MODEL)

    assert excinfo.value.code == exit_code

    if severity is None:
        chatops_spy.assert_not_called()
    else:
        chatops_spy.assert_called_once()
        # severity is only passed explicitly for the outage path; otherwise it defaults.
        assert chatops_spy.call_args.kwargs.get("severity", "critical") == severity
        # The message must name the model and the source - NOAA's used to be a broken
        # f-string that posted the literal text "{sys.argv[1]}" to chatops.
        message = chatops_spy.call_args.args[0]
        assert MODEL in message
        assert SOURCE in message


def test_run_model_job_applies_data_retention_policy_on_success(mocker, monkeypatch):
    """The retention policy only runs when the job got that far."""
    retention = MagicMock()
    monkeypatch.setattr(model_job_runner, "apply_data_retention_policy", retention)
    mocker.patch.object(model_job_runner, "send_chatops_notification")

    with pytest.raises(SystemExit):
        run_model_job(lambda: None, source=SOURCE, model=MODEL)

    retention.assert_called_once()


def test_judge_run_warns_about_connection_errors(caplog):
    """A partial outage still gets a line in the log, even though the run succeeds."""
    job = FakeJob(files_processed=10, connection_error_count=5, exception_count=0)

    with caplog.at_level("WARNING"):
        judge_run(job, source=SOURCE, model=MODEL)

    assert "5 connection error(s)" in caplog.text


def test_sys_argv_is_not_read_by_the_runner():
    """The runner takes the model as an argument - it must not reach back into sys.argv."""
    original = sys.argv
    sys.argv = ["argv"]  # no model argument at all
    try:
        job = FakeJob(files_processed=0, connection_error_count=1, exception_count=0)
        with pytest.raises(NoFilesProcessed) as excinfo:
            judge_run(job, source=SOURCE, model=MODEL)
        assert MODEL in str(excinfo.value)
    finally:
        sys.argv = original
