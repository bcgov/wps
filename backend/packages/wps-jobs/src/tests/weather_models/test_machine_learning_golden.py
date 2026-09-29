"""Golden test: bias adjusted predictions on seeded synthetic data must match recorded values.

The expected values in ml_golden_predictions.json were recorded from the implementation before the
machine learning refactor, so this guards against unintended changes in predictions. If a change is
intended, regenerate them with:

    python -m tests.weather_models.test_machine_learning_golden
"""

import json
import math
import os
import random
from datetime import datetime, timedelta, timezone

import pytest
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModel,
    WeatherStationModelPrediction,
)
from weather_model_jobs import machine_learning
from weather_model_jobs.machine_learning import StationMachineLearning

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "ml_golden_predictions.json")
# seed-step: step 1 is an hourly model (HRDPS, RDPS), step 3 is 3-hourly with noon interpolation (GDPS)
CASES = [(seed, step) for seed in range(2) for step in (1, 3)]


class ActualPrecip:
    def __init__(self, day, actual_precip_24h):
        self.day = day
        self.actual_precip_24h = actual_precip_24h


def _maybe(rng, value, p_none=0.05, p_nan=0.0):
    r = rng.random()
    if r < p_none:
        return None
    if r < p_none + p_nan:
        return math.nan
    return value


def _build_rows(seed: int, step: int):
    """Hourly actuals for 19 days, predictions every `step` hours, some from 2 model runs."""
    rng = random.Random(seed)
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(19 * 24):
        ts = start + timedelta(hours=i)
        actual = HourlyActual(
            weather_date=ts,
            temperature=_maybe(rng, rng.uniform(-5, 35), p_nan=0.02),
            relative_humidity=_maybe(rng, rng.uniform(5, 105), p_nan=0.02),
            wind_speed=_maybe(rng, rng.uniform(0, 40), p_nan=0.02),
            wind_direction=_maybe(rng, rng.uniform(0, 360), p_nan=0.02),
            temp_valid=True,
            rh_valid=True,
        )
        if ts.hour % step != 0:
            rows.append((actual, None))
            continue
        # newest run first, like the real query; the older run must be ignored
        for _ in range(rng.choice([1, 1, 2])):
            prediction = ModelRunPrediction(
                prediction_timestamp=ts,
                tmp_tgl_2=_maybe(rng, rng.uniform(-5, 35)),
                rh_tgl_2=_maybe(rng, rng.uniform(5, 100)),
                wind_tgl_10=_maybe(rng, rng.uniform(0, 40)),
                wdir_tgl_10=_maybe(rng, rng.uniform(0, 360)),
                apcp_sfc_0=_maybe(rng, rng.uniform(0, 10)),
            )
            rows.append((actual, prediction))
    return rows


def _build_precip(seed: int):
    rng = random.Random(seed + 1000)
    actuals, predicted = [], []
    for d in range(19):
        day = datetime(2026, 8, 1, 20, tzinfo=timezone.utc) + timedelta(days=d)
        actuals.append(ActualPrecip(day, _maybe(rng, rng.uniform(0, 20), p_nan=0.05)))
        for _ in range(rng.choice([1, 2])):
            predicted.append(
                WeatherStationModelPrediction(
                    prediction_timestamp=day,
                    precip_24h=_maybe(rng, rng.uniform(0, 20), p_nan=0.05),
                )
            )
    return actuals, predicted


def _predictions(monkeypatch, seed: int, step: int):
    """Train on the seeded data and return [temp, rh, wind speed, wind dir, precip] rows."""
    rows = _build_rows(seed, step)
    precip_actuals, precip_predicted = _build_precip(seed)
    monkeypatch.setattr(
        machine_learning, "get_actuals_left_outer_join_with_predictions", lambda *a: rows
    )
    monkeypatch.setattr(
        machine_learning, "get_accumulated_precip_by_24h_interval", lambda *a: precip_actuals
    )
    monkeypatch.setattr(machine_learning, "get_predicted_daily_precip", lambda *a: precip_predicted)

    machine = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[0, 0],
        station_code=1,
        max_learn_date=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )
    machine.learn()

    rng = random.Random(seed + 2000)
    out = []
    for hour in range(24):
        ts = datetime(2026, 8, 21, hour, tzinfo=timezone.utc)
        for _ in range(5):
            t, rh, ws, wd, p = (
                rng.uniform(-5, 35),
                rng.uniform(0, 110),
                rng.uniform(0, 40),
                rng.uniform(0, 360),
                rng.uniform(0, 20),
            )
            out.append(
                [
                    machine.predict_temperature(t, ts),
                    machine.predict_rh(rh, ts),
                    machine.predict_wind_speed(ws, ts),
                    machine.predict_wind_direction(ws, wd, ts),
                    machine.predict_precipitation(p, ts),
                ]
            )
        out.append(
            [
                machine.predict_temperature(None, ts),
                machine.predict_rh(None, ts),
                machine.predict_wind_speed(None, ts),
                machine.predict_wind_direction(None, 90, ts),
                machine.predict_precipitation(None, ts),
            ]
        )
    return out


@pytest.mark.parametrize("seed, step", CASES)
def test_predictions_match_golden(monkeypatch, seed, step):
    with open(GOLDEN_PATH) as f:
        expected = json.load(f)[f"{seed}-{step}"]

    actual = _predictions(monkeypatch, seed, step)

    assert len(actual) == len(expected)
    for expected_row, actual_row in zip(expected, actual):
        assert actual_row == pytest.approx(expected_row, rel=1e-9, abs=1e-9)


if __name__ == "__main__":
    with pytest.MonkeyPatch.context() as mp:
        golden = {f"{seed}-{step}": _predictions(mp, seed, step) for seed, step in CASES}
    with open(GOLDEN_PATH, "w") as f:
        json.dump(golden, f, indent=0)
    print(f"wrote {GOLDEN_PATH}")
