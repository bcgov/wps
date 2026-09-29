"""Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.

For each station and weather model, every variable gets one linear regression per hour of the day,
trained on model predictions against observed values over the last MAX_DAYS_TO_LEARN days.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from logging import getLogger
from typing import Callable, Iterator, List, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session
from wps_shared.db.crud.observations import (
    get_accumulated_precip_by_24h_interval,
    get_actuals_left_outer_join_with_predictions,
    get_predicted_daily_precip,
)
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel
from wps_shared.weather_models import SCALAR_MODEL_VALUE_KEYS

from weather_model_jobs.utils.interpolate import construct_interpolated_noon_prediction
from weather_model_jobs.utils.wind_direction_utils import calculate_wind_dir_from_u_v, compute_u_v

logger = getLogger(__name__)

# Number of days of historical actual data to learn from when training model.
# Experimentation has shown that about two weeks worth of data starts giving fairly good results
# compared to human forecasters.
MAX_DAYS_TO_LEARN = 19


def _values(*values: Optional[float]) -> Optional[List[float]]:
    """Return the values as regression features, or None if any is missing or NaN."""
    if any(value is None or math.isnan(value) for value in values):
        return None
    return [float(value) for value in values]


def _u_v(wind_speed: Optional[float], wind_direction: Optional[float]) -> Optional[List[float]]:
    """Wind direction is learned as u, v components, see
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv"""
    if _values(wind_speed, wind_direction) is None:
        return None
    return compute_u_v(wind_speed, wind_direction)


@dataclass(frozen=True)
class Target:
    """A variable to bias adjust: how to read its features from a prediction and an observation."""

    predicted: Callable[[ModelRunPrediction], Optional[List[float]]]
    observed: Callable[[HourlyActual], Optional[List[float]]]
    learn_from_interpolated_noon: bool = True


TARGETS = {
    "temperature": Target(
        predicted=lambda p: _values(p.tmp_tgl_2), observed=lambda a: _values(a.temperature)
    ),
    "relative_humidity": Target(
        predicted=lambda p: _values(p.rh_tgl_2), observed=lambda a: _values(a.relative_humidity)
    ),
    "wind_speed": Target(
        predicted=lambda p: _values(p.wind_tgl_10), observed=lambda a: _values(a.wind_speed)
    ),
    # Wind direction has never learned from the interpolated noon sample for 3-hourly models
    # (e.g. GDPS), because its noon sample was built without wind speed. Kept as-is so this
    # refactor doesn't change predictions.
    "wind_direction": Target(
        predicted=lambda p: _u_v(p.wind_tgl_10, p.wdir_tgl_10),
        observed=lambda a: _u_v(a.wind_speed, a.wind_direction),
        learn_from_interpolated_noon=False,
    ),
}


class HourlyRegression:
    """One linear regression per hour of the day. Hours without samples predict None."""

    def __init__(self):
        self._samples: dict[int, tuple[list, list]] = defaultdict(lambda: ([], []))
        self._models: dict[int, LinearRegression] = {}

    def add(self, hour: int, x: List[float], y: List[float]):
        xs, ys = self._samples[hour]
        xs.append(x)
        ys.append(y)

    def fit(self):
        self._models = {
            hour: LinearRegression().fit(np.array(xs), np.array(ys))
            for hour, (xs, ys) in self._samples.items()
        }

    def predict(self, hour: int, x: List[float]) -> Optional[np.ndarray]:
        model = self._models.get(hour)
        if model is None:
            return None
        return model.predict([x])[0]


def paired_samples(
    data: list[tuple[HourlyActual, Optional[ModelRunPrediction]]],
) -> Iterator[tuple[ModelRunPrediction, HourlyActual, bool]]:
    """Yield (prediction, actual, is_interpolated_noon) pairs to learn from.

    Rows are ordered by actual, newest model run first, so only the first prediction per actual is
    used. Models with a gap at 20:00 UTC (solar noon in B.C., e.g. GDPS) get a noon prediction
    interpolated from 18:00 and 21:00.
    """
    prev_actual = None
    prev_prediction = None
    for actual, prediction in data:
        if prev_actual != actual and prediction is not None:
            if (
                prev_actual is not None
                and prev_prediction is not None
                and prev_actual.weather_date.hour == 20
                and prediction.prediction_timestamp.hour == 21
                and prev_prediction.prediction_timestamp.hour == 18
            ):
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS
                )
                yield noon_prediction, prev_actual, True
            yield prediction, actual, False
            prev_prediction = prediction
        prev_actual = actual


class StationMachineLearning:
    """Wrap away machine learning in an easy to use class."""

    def __init__(
        self,
        session: Session,
        model: PredictionModel,
        target_coordinate: List[float],
        station_code: int,
        max_learn_date: datetime,
    ):
        """
        : param session: Database session.
        : param model: Prediction model, e.g. GDPS
        : param target_coordinate: Coordinate we're interested in .
        : param station_code: Code of the weather station.
        : param max_learn_date: Maximum date up to which to learn.
        """
        self.session = session
        self.model = model
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.max_learn_date = max_learn_date
        self.regressions = {name: HourlyRegression() for name in TARGETS}
        self.precip_regression = HourlyRegression()

    def _learn_models(self, start_date: datetime):
        data = get_actuals_left_outer_join_with_predictions(
            self.session, self.model.id, self.station_code, start_date, self.max_learn_date
        )
        for prediction, actual, is_interpolated_noon in paired_samples(list(data)):
            for name, target in TARGETS.items():
                if is_interpolated_noon and not target.learn_from_interpolated_noon:
                    continue
                x = target.predicted(prediction)
                y = target.observed(actual)
                if x is None or y is None:
                    logger.debug(
                        "skipping %s sample at %s, missing value", name, actual.weather_date
                    )
                    continue
                self.regressions[name].add(actual.weather_date.hour, x, y)
        for regression in self.regressions.values():
            regression.fit()

    def _learn_precip_model(self, start_date: datetime):
        """Learn 24 hour precip, which is based on 24 hour periods ending at 20:00 UTC."""
        start_datetime = datetime(
            start_date.year, start_date.month, start_date.day, 20, tzinfo=timezone.utc
        )
        # NOTE: this is tomorrow at 20:00 UTC (subtracting -1 days), although a previous comment
        # said yesterday. Kept as-is to not change what precip is learned from.
        end_date = date.today() - timedelta(days=-1)
        end_datetime = datetime(
            end_date.year, end_date.month, end_date.day, 20, tzinfo=timezone.utc
        )
        actual_daily_precip = get_accumulated_precip_by_24h_interval(
            self.session, self.station_code, start_datetime, end_datetime
        )
        predicted_daily_precip = get_predicted_daily_precip(
            self.session, self.model, self.station_code, start_datetime, end_datetime
        )

        predicted_by_day = defaultdict(list)
        for predicted in predicted_daily_precip:
            predicted_by_day[predicted.prediction_timestamp].append(predicted)
        for actual in actual_daily_precip:
            y = _values(actual.actual_precip_24h)
            for predicted in predicted_by_day.get(actual.day, []):
                x = _values(predicted.precip_24h)
                if x is not None and y is not None:
                    self.precip_regression.add(actual.day.hour, x, y)
        self.precip_regression.fit()

    def learn(self):
        start_date = self.max_learn_date - timedelta(days=MAX_DAYS_TO_LEARN)
        self._learn_models(start_date)
        self._learn_precip_model(start_date)

    @staticmethod
    def _predict(
        regression: HourlyRegression, name: str, x: Optional[List[float]], timestamp: datetime
    ) -> Optional[np.ndarray]:
        if x is None:
            logger.warning("model %s for %s was None or NaN", name, timestamp)
            return None
        return regression.predict(timestamp.hour, x)

    def predict_temperature(self, model_temperature: float, timestamp: datetime):
        """Bias adjusted temperature for the model temperature at timestamp, or None."""
        y = self._predict(
            self.regressions["temperature"], "temperature", _values(model_temperature), timestamp
        )
        return None if y is None else float(y[0])

    def predict_rh(self, model_rh: float, timestamp: datetime):
        """Bias adjusted RH for the model RH at timestamp, or None. Clamped to 0-100."""
        y = self._predict(
            self.regressions["relative_humidity"], "relative humidity", _values(model_rh), timestamp
        )
        return None if y is None else float(min(max(0, y[0]), 100))

    def predict_wind_speed(self, model_wind_speed: float, timestamp: datetime):
        """Bias adjusted wind speed for the model wind speed at timestamp, or None. Never negative."""
        y = self._predict(
            self.regressions["wind_speed"], "wind speed", _values(model_wind_speed), timestamp
        )
        return None if y is None else float(max(0, y[0]))

    def predict_wind_direction(
        self, model_wind_speed: float, model_wind_dir: int, timestamp: datetime
    ):
        """Bias adjusted wind direction for the model wind speed and direction at timestamp, or None."""
        y = self._predict(
            self.regressions["wind_direction"],
            "wind speed or direction",
            _u_v(model_wind_speed, model_wind_dir),
            timestamp,
        )
        return None if y is None else float(calculate_wind_dir_from_u_v(y[0], y[1]))

    def predict_precipitation(self, model_precipitation: float, timestamp: datetime):
        """Bias adjusted 24 hour precip for the model 24 hour precip at timestamp, or None. Never negative."""
        y = self._predict(
            self.precip_regression, "precipitation", _values(model_precipitation), timestamp
        )
        return None if y is None else float(max(0, y[0]))
