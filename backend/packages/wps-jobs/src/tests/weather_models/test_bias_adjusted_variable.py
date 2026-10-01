import math
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel

from weather_model_jobs import bias_adjusted_variable
from weather_model_jobs.bias_adjusted_variable import (
    BIAS_ADJUSTED_VARIABLES,
    TEMPERATURE,
    DailyPrecipVariable,
    HourlyVariable,
    LearningContext,
    Sample,
    features,
    u_v,
)
from weather_model_jobs.utils.wind_direction_utils import compute_u_v


def _context() -> LearningContext:
    return LearningContext(
        session=None,
        model=PredictionModel(id=1),
        station_code=1,
        start_date=datetime(2020, 10, 1, tzinfo=timezone.utc),
        end_date=datetime(2020, 10, 20, tzinfo=timezone.utc),
    )


def _prediction(hour: int, temperature: float) -> ModelRunPrediction:
    return ModelRunPrediction(
        prediction_timestamp=datetime(2020, 10, 10, hour),
        tmp_tgl_2=temperature,
        rh_tgl_2=50,
        wind_tgl_10=10,
        wdir_tgl_10=180,
    )


def _actual(hour: int, temperature=None) -> HourlyActual:
    return HourlyActual(weather_date=datetime(2020, 10, 10, hour), temperature=temperature)


def _gdps_rows():
    """3-hourly model: predictions at 18:00 and 21:00, but an actual at 20:00 with none."""
    return [
        (_actual(18, 11), _prediction(18, 10)),
        (_actual(20, 15), None),
        (_actual(21, 17), _prediction(21, 16)),
    ]


@pytest.mark.parametrize(
    "raw, expected",
    [
        ((1, 2), [1.0, 2.0]),
        ((1, None), None),
        ((math.nan,), None),
    ],
)
def test_features(raw, expected):
    assert features(*raw) == expected


def test_u_v():
    assert u_v(10, 180) == compute_u_v(10, 180)
    assert u_v(None, 180) is None
    assert u_v(10, math.nan) is None


def _mock_query(monkeypatch, rows):
    monkeypatch.setattr(
        bias_adjusted_variable, "get_actuals_left_outer_join_with_predictions", lambda *a: rows
    )


def test_hourly_pairs_uses_newest_model_run_per_actual(monkeypatch):
    actual = _actual(18, 11)
    newest, older = _prediction(18, 10), _prediction(18, 5)
    _mock_query(monkeypatch, [(actual, newest), (actual, older)])

    assert _context().hourly_pairs == [(newest, actual, False)]


def test_hourly_pairs_interpolates_noon_for_3_hourly_models(monkeypatch):
    _mock_query(monkeypatch, _gdps_rows())

    pairs = _context().hourly_pairs

    assert [(a.weather_date.hour, is_noon) for _, a, is_noon in pairs] == [
        (18, False),
        (20, True),
        (21, False),
    ]
    noon_prediction = pairs[1][0]
    # 10 at 18:00 to 16 at 21:00, two thirds of the way
    assert noon_prediction.tmp_tgl_2 == pytest.approx(14)


def test_hourly_variable_samples(monkeypatch):
    rows = [*_gdps_rows(), (_actual(22), _prediction(22, 12))]  # no observed temperature at 22:00
    _mock_query(monkeypatch, rows)
    context = _context()

    assert list(TEMPERATURE.samples(context)) == [
        Sample(18, [10.0], [11.0]),
        Sample(20, [pytest.approx(14)], [15.0]),
        Sample(21, [16.0], [17.0]),
    ]
    no_noon = HourlyVariable(TEMPERATURE.predicted, TEMPERATURE.observed, False)
    assert [s.hour for s in no_noon.samples(context)] == [18, 21]


def test_hourly_pairs_queried_once_for_all_hourly_variables(monkeypatch):
    calls = []

    def query(*args):
        calls.append(args)
        return _gdps_rows()

    monkeypatch.setattr(
        bias_adjusted_variable, "get_actuals_left_outer_join_with_predictions", query
    )
    context = _context()

    for variable in BIAS_ADJUSTED_VARIABLES:
        if isinstance(variable, HourlyVariable):
            list(variable.samples(context))

    assert len(calls) == 1


def test_daily_precip_variable_samples(monkeypatch):
    day_1 = datetime(2020, 10, 10, 20, tzinfo=timezone.utc)
    day_2 = datetime(2020, 10, 11, 20, tzinfo=timezone.utc)
    day_3 = datetime(2020, 10, 12, 20, tzinfo=timezone.utc)
    actuals = [
        SimpleNamespace(day=day_1, actual_precip_24h=5),
        SimpleNamespace(day=day_2, actual_precip_24h=None),  # missing observation
        SimpleNamespace(day=day_3, actual_precip_24h=1),  # no model prediction
    ]
    predicted = [
        # two model runs for day 1, both are learned from
        SimpleNamespace(prediction_timestamp=day_1, precip_24h=4),
        SimpleNamespace(prediction_timestamp=day_1, precip_24h=6),
        SimpleNamespace(prediction_timestamp=day_1, precip_24h=math.nan),
        SimpleNamespace(prediction_timestamp=day_2, precip_24h=2),
    ]
    monkeypatch.setattr(
        bias_adjusted_variable, "get_accumulated_precip_by_24h_interval", lambda *a: actuals
    )
    monkeypatch.setattr(bias_adjusted_variable, "get_predicted_daily_precip", lambda *a: predicted)

    assert list(DailyPrecipVariable().samples(_context())) == [
        Sample(20, [4.0], [5.0]),
        Sample(20, [6.0], [5.0]),
    ]
