from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from weather_model_jobs import bias_adjusted_variable, machine_learning
from weather_model_jobs.bias_adjusted_variable import (
    get_actuals_paired_with_predictions,
    get_predicted_daily_precip,
)
from weather_model_jobs.model_history import DailyPrecip, ModelHistory
from weather_model_jobs.model_values import ModelValues
from wps_shared.weather_models import ModelEnum
from wps_weather_data.actuals import Observation, StationObservations
from wps_weather_data.runs import RunsTable

EARLY_RUN = datetime(2026, 11, 10, 0, tzinfo=UTC)
LATE_RUN = datetime(2026, 11, 10, 12, tzinfo=UTC)
AT_1800 = datetime(2026, 11, 10, 18, tzinfo=UTC)
AT_2000 = datetime(2026, 11, 10, 20, tzinfo=UTC)
AT_2100 = datetime(2026, 11, 10, 21, tzinfo=UTC)
NEXT_2000 = datetime(2026, 11, 11, 20, tzinfo=UTC)
HOURLY_FROM = datetime(2026, 11, 10, tzinfo=UTC)
HOURLY_TO = datetime(2026, 11, 11, tzinfo=UTC)
DAILY_FROM = datetime(2026, 11, 10, 20, tzinfo=UTC)
DAILY_TO = datetime(2026, 11, 12, 20, tzinfo=UTC)


def row(time, temperature, *, is_interpolated=False, precip_24h=None, station_code=322):
    return {
        "station_code": station_code,
        "prediction_timestamp": time,
        "tmp_tgl_2": temperature,
        "rh_tgl_2": 50.0,
        "wind_tgl_10": 5.0,
        "wdir_tgl_10": 180.0,
        "precip_24h": precip_24h,
        "is_interpolated": is_interpolated,
    }


@pytest.fixture
def runs(tmp_path):
    return RunsTable(str(tmp_path / "runs"))


def read(runs):
    return ModelHistory.read(runs, ModelEnum.GDPS, HOURLY_FROM, HOURLY_TO, DAILY_FROM, DAILY_TO)


def test_no_table_gives_no_history(runs):
    history = read(runs)

    assert history.newest_value(322, AT_1800) is None
    assert history.daily_precip(322, DAILY_FROM, DAILY_TO) == []


def test_newest_run_per_time_gives_the_model_values(runs):
    runs.append_run(ModelEnum.GDPS, EARLY_RUN, [row(AT_1800, 10.0), row(AT_2100, 11.0)])
    runs.append_run(ModelEnum.GDPS, LATE_RUN, [row(AT_1800, 20.0)])

    history = read(runs)

    assert history.newest_value(322, AT_1800).tmp_tgl_2 == 20.0
    # The late run did not predict 21:00, so the early run's value stands.
    assert history.newest_value(322, AT_2100).tmp_tgl_2 == 11.0
    value = history.newest_value(322, AT_1800)
    assert isinstance(value, ModelValues)
    assert (value.rh_tgl_2, value.wind_tgl_10, value.wdir_tgl_10) == (50.0, 5.0, 180.0)


def test_interpolated_rows_are_not_model_values(runs):
    runs.append_run(ModelEnum.GDPS, EARLY_RUN, [row(AT_2000, 10.0, is_interpolated=True)])

    assert read(runs).newest_value(322, AT_2000) is None


def test_rows_of_unknown_origin_count_except_at_2000(runs):
    runs.append_run(
        ModelEnum.GDPS,
        EARLY_RUN,
        [row(AT_1800, 10.0, is_interpolated=None), row(AT_2000, 11.0, is_interpolated=None)],
    )

    history = read(runs)

    assert history.newest_value(322, AT_1800).tmp_tgl_2 == 10.0
    assert history.newest_value(322, AT_2000) is None


def test_a_reprocessed_run_gives_its_newest_version(runs):
    runs.append_run(ModelEnum.GDPS, EARLY_RUN, [row(AT_1800, 10.0)], ingested_at=EARLY_RUN)
    runs.append_run(ModelEnum.GDPS, EARLY_RUN, [row(AT_1800, 12.0)], ingested_at=LATE_RUN)

    assert read(runs).newest_value(322, AT_1800).tmp_tgl_2 == 12.0


def test_daily_precip_keeps_every_runs_2000_prediction(runs):
    runs.append_run(
        ModelEnum.GDPS,
        EARLY_RUN,
        [
            row(AT_1800, 10.0, precip_24h=1.0),
            row(AT_2000, 10.0, precip_24h=2.0, is_interpolated=True),
            row(NEXT_2000, 10.0, precip_24h=3.0),
        ],
    )
    runs.append_run(ModelEnum.GDPS, LATE_RUN, [row(AT_2000, 10.0, precip_24h=4.0)])
    runs.append_run(ModelEnum.RDPS, LATE_RUN, [row(AT_2000, 10.0, precip_24h=5.0)])

    history = read(runs)

    # Interpolated or not, every GDPS run's 20:00 prediction is a sample; 18:00 and RDPS are not.
    precip = sorted(
        (p.prediction_timestamp, p.precip_24h)
        for p in history.daily_precip(322, DAILY_FROM, DAILY_TO)
    )
    assert precip == [(AT_2000, 2.0), (AT_2000, 4.0), (NEXT_2000, 3.0)]
    # The end of the range is left out.
    before_next = sorted(p.precip_24h for p in history.daily_precip(322, DAILY_FROM, NEXT_2000))
    assert before_next == [2.0, 4.0]


def observation(time, temperature=12.0):
    return Observation(time, temperature, 50.0, 5.0, 180.0, 0.0)


def test_actuals_are_paired_with_the_newest_model_values():
    at_1800 = observation(AT_1800)
    at_1900 = observation(AT_1800 + timedelta(hours=1))
    observations = StationObservations({322: [at_1800, at_1900]})
    prediction = ModelValues(station_code=322, prediction_timestamp=AT_1800, tmp_tgl_2=10.0)
    history = ModelHistory({322: {AT_1800: prediction}}, {})

    rows = get_actuals_paired_with_predictions(observations, history, 322, HOURLY_FROM, HOURLY_TO)

    # No run predicted 19:00, so that observation is left out, as the database join did.
    assert rows == [(at_1800, prediction)]


def test_predicted_daily_precip_comes_from_the_history():
    precip = DailyPrecip(AT_2000, 2.0)
    history = ModelHistory({}, {322: [precip]})

    assert get_predicted_daily_precip(history, 322, DAILY_FROM, DAILY_TO) == [precip]
    assert get_predicted_daily_precip(history, 209, DAILY_FROM, DAILY_TO) == []


def test_read_model_history_covers_what_training_learns_from(monkeypatch):
    read_history = MagicMock()
    monkeypatch.setattr(machine_learning.ModelHistory, "read", read_history)
    runs = MagicMock()
    max_learn_date = datetime(2026, 11, 20, 12, tzinfo=UTC)

    machine_learning.read_model_history(runs, ModelEnum.GDPS, max_learn_date)

    start = max_learn_date - timedelta(days=machine_learning.MAX_DAYS_TO_LEARN)
    daily_from, daily_to = bias_adjusted_variable.daily_precip_window(start)
    read_history.assert_called_once_with(
        runs, ModelEnum.GDPS, start, max_learn_date, daily_from, daily_to
    )


def test_read_observations_covers_training_and_the_day_before_the_run(monkeypatch):
    read = MagicMock()
    monkeypatch.setattr(machine_learning.StationObservations, "read", read)
    by_time = MagicMock()
    max_learn_date = datetime(2026, 11, 20, 12, tzinfo=UTC)

    machine_learning.read_observations(by_time, max_learn_date)

    start = max_learn_date - timedelta(days=machine_learning.MAX_DAYS_TO_LEARN)
    daily_from, daily_to = bias_adjusted_variable.daily_precip_window(start)
    read.assert_called_once_with(
        by_time, min(start, daily_from - timedelta(hours=24)), max(max_learn_date, daily_to)
    )
