import urllib.error
from datetime import UTC, datetime, timedelta

import pytest

from wps_weather_data.grids import models
from wps_weather_data.grids.job import keep_grids, run_times
from wps_weather_data.tests.grid_helpers import MODEL, fake_datamart, store

# 19:30 UTC on 19 November: the 18Z run is the latest.
NOW = datetime(2026, 11, 19, 19, 30, tzinfo=UTC)


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=UTC)


def test_runs_of_the_last_day_oldest_first():
    # From 19:30 on the 18th: the 18th's 18Z run started before that.
    assert run_times(MODEL, NOW) == [at(19, 0), at(19, 6), at(19, 12), at(19, 18)]


def test_new_runs_go_to_recent_and_the_daily_run_to_history(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    written = keep_grids(MODEL, recent, history, NOW)

    assert written == run_times(MODEL, NOW)
    assert recent.run_times() == written
    # Only the 18Z run, the model's last full-length run of the day.
    assert history.run_times() == [at(19, 18)]


def test_runs_already_stored_are_not_fetched_again(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")
    keep_grids(MODEL, recent, history, NOW)
    asked = fake_datamart(monkeypatch)

    assert keep_grids(MODEL, recent, history, NOW) == []
    assert asked == []


def test_a_run_not_all_published_waits_for_the_next_time(monkeypatch, tmp_path):
    fake_datamart(monkeypatch, unpublished={"20261119T18"})
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    keep_grids(MODEL, recent, history, NOW)
    assert at(19, 18) not in recent.run_times()
    assert history.run_times() == []

    fake_datamart(monkeypatch)
    assert keep_grids(MODEL, recent, history, NOW) == [at(19, 18)]
    assert history.run_times() == [at(19, 18)]


def test_the_daily_run_missing_from_history_is_written_there(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")
    keep_grids(MODEL, recent, history, NOW)
    history = store(tmp_path, "history-new")

    assert keep_grids(MODEL, recent, history, NOW) == [at(19, 18)]
    assert history.run_times() == [at(19, 18)]


def test_runs_older_than_two_days_leave_recent(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")
    keep_grids(MODEL, recent, history, NOW)

    keep_grids(MODEL, recent, history, NOW + timedelta(days=2))

    assert min(recent.run_times()) >= NOW
    assert at(19, 18) in history.run_times()


@pytest.mark.parametrize("error", [500, 403])
def test_other_download_errors_fail_the_job(monkeypatch, tmp_path, error):
    def download(url, path):
        raise urllib.error.HTTPError(url, error, "error", None, None)

    fake_datamart(monkeypatch)
    monkeypatch.setattr(models, "download", download)
    with pytest.raises(urllib.error.HTTPError):
        keep_grids(MODEL, store(tmp_path, "recent"), store(tmp_path, "history"), NOW)
