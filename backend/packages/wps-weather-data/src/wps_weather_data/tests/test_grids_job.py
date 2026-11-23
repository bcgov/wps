import urllib.error
from datetime import UTC, datetime, timedelta

import pytest

from wps_weather_data.grids import models
from wps_weather_data.grids.job import keep_grids, run_times
from wps_weather_data.tests.grid_helpers import MODEL, fake_datamart, refuse_writes, store

# 19:30 UTC on 19 November: the 18Z run is the latest.
NOW = datetime(2026, 11, 19, 19, 30, tzinfo=UTC)


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=UTC)


def test_runs_of_the_last_day_oldest_first():
    # From 19:30 on the 18th: the 18th's 18Z run started before that.
    assert run_times(MODEL, NOW) == [at(19, 0), at(19, 6), at(19, 12), at(19, 18)]


def test_gdps_runs_twice_a_day_at_three_hour_steps():
    gdps = models.MODELS["GDPS"]

    assert run_times(gdps, NOW) == [at(19, 0), at(19, 12)]
    assert gdps.history_run_hour in gdps.run_hours
    assert (gdps.hours[0], gdps.hours[1], gdps.hours[-1]) == (0, 3, 240)
    assert gdps.file_url(at(19, 12), 240, gdps.variables[0]) == (
        "https://dd.weather.gc.ca/today/model_gdps/15km/12/240/"
        "20261119T12Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT240H.grib2"
    )


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


@pytest.mark.parametrize("step", ["add", "commit"])
def test_a_stuck_recent_store_does_not_hold_up_history(monkeypatch, tmp_path, step):
    downloaded = fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")
    refuse_writes(monkeypatch, recent, step)

    with pytest.raises(ExceptionGroup, match="TEST recent; stored 1 runs"):
        keep_grids(MODEL, recent, history, NOW)

    assert history.run_times() == [at(19, 18)]
    assert recent.run_times() == []
    # Once recent has failed, the runs only it keeps are not downloaded.
    assert {url.split("/")[-1][:11] for url in downloaded} == {"20261119T00", "20261119T18"}


def test_a_stuck_history_store_does_not_hold_up_recent(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")
    refuse_writes(monkeypatch, history, "commit")

    with pytest.raises(ExceptionGroup, match="TEST history"):
        keep_grids(MODEL, recent, history, NOW)

    assert recent.run_times() == run_times(MODEL, NOW)


def test_a_store_that_cannot_be_read_does_not_hold_up_the_other(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    def unreadable():
        raise OSError("unreadable")

    monkeypatch.setattr(recent, "run_times", unreadable)
    with pytest.raises(ExceptionGroup, match="TEST recent"):
        keep_grids(MODEL, recent, history, NOW)

    assert history.run_times() == [at(19, 18)]


def test_failing_to_delete_old_runs_fails_the_job_after_the_runs_are_kept(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    def refuse(cutoff):
        raise OSError("refused")

    monkeypatch.setattr(recent, "delete_runs_before", refuse)
    with pytest.raises(ExceptionGroup, match="TEST recent; stored 4 runs"):
        keep_grids(MODEL, recent, history, NOW)

    assert recent.run_times() == run_times(MODEL, NOW)
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


def test_a_run_whose_files_vanish_part_way_is_retried_next_time(monkeypatch, tmp_path):
    fake_datamart(monkeypatch, vanished={"20261119T18"})
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    written = keep_grids(MODEL, recent, history, NOW)

    assert at(19, 18) not in written
    assert at(19, 18) not in recent.run_times()
    assert history.run_times() == []


def test_an_unpublished_run_is_not_downloaded(monkeypatch, tmp_path):
    downloaded = fake_datamart(monkeypatch, unpublished={"20261119T18"})

    keep_grids(MODEL, store(tmp_path, "recent"), store(tmp_path, "history"), NOW)

    assert not any("20261119T18Z" in url for url in downloaded)
