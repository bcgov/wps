"""Variables that StationMachineLearning bias adjusts, and how each one's training samples are built."""

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import cached_property
from logging import getLogger
from typing import Callable, Iterator, List, Optional, Protocol

from sqlalchemy.orm import Session
from weather_model_jobs.utils.interpolate import construct_interpolated_noon_prediction
from weather_model_jobs.utils.wind_direction_utils import compute_u_v
from wps_shared.db.crud.observations import (
    get_accumulated_precip_by_24h_interval,
    get_actuals_left_outer_join_with_predictions,
    get_predicted_daily_precip,
)
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel
from wps_shared.weather_models import SCALAR_MODEL_VALUE_KEYS

logger = getLogger(__name__)


def features(*raw: Optional[float]) -> Optional[List[float]]:
    """Return the values as a regression row (features or observed values), or None if any is
    missing or NaN."""
    if any(value is None or math.isnan(value) for value in raw):
        return None
    return [float(value) for value in raw]


def u_v(wind_speed: Optional[float], wind_direction: Optional[float]) -> Optional[List[float]]:
    """Wind direction is learned as u, v components, see
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv"""
    if features(wind_speed, wind_direction) is None:
        return None
    return compute_u_v(wind_speed, wind_direction)


@dataclass(frozen=True)
class Sample:
    """One regression training sample: model features x and observed values y at an hour of the day."""

    hour: int
    x: List[float]
    y: List[float]


@dataclass
class LearningContext:
    """The station, model and date range to learn from, shared by every variable being learned."""

    session: Session
    model: PredictionModel
    station_code: int
    start_date: datetime
    end_date: datetime

    @cached_property
    def hourly_pairs(self) -> list[tuple[ModelRunPrediction, HourlyActual, bool]]:
        """Hourly (prediction, actual, is_interpolated_noon) pairs to learn from, queried once for
        all hourly variables.

        Rows are ordered by actual, newest model run first, so only the first prediction per actual
        is used. Models with a gap at 20:00 UTC (solar noon in B.C., e.g. GDPS) get a noon
        prediction interpolated from 18:00 and 21:00.
        """
        rows = get_actuals_left_outer_join_with_predictions(
            self.session, self.model.id, self.station_code, self.start_date, self.end_date
        )
        pairs = []
        prev_actual = None
        prev_prediction = None
        for actual, prediction in rows:
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
                    pairs.append((noon_prediction, prev_actual, True))
                pairs.append((prediction, actual, False))
                prev_prediction = prediction
            prev_actual = actual
        return pairs


class BiasAdjustedVariable(Protocol):
    """A variable to bias adjust: supplies its own training samples for the station being learned."""

    def samples(self, context: LearningContext) -> Iterator[Sample]: ...


@dataclass(frozen=True)
class HourlyVariable(BiasAdjustedVariable):
    """A variable learned from hourly model predictions paired with hourly observations."""

    predicted: Callable[[ModelRunPrediction], Optional[List[float]]]
    observed: Callable[[HourlyActual], Optional[List[float]]]
    learn_from_interpolated_noon: bool = True

    def samples(self, context: LearningContext) -> Iterator[Sample]:
        for prediction, actual, is_interpolated_noon in context.hourly_pairs:
            if is_interpolated_noon and not self.learn_from_interpolated_noon:
                continue
            x = self.predicted(prediction)
            y = self.observed(actual)
            if x is None or y is None:
                logger.debug("skipping sample at %s, missing value", actual.weather_date)
                continue
            yield Sample(actual.weather_date.hour, x, y)


class DailyPrecipVariable(BiasAdjustedVariable):
    """24 hour precip, learned from 24 hour periods ending at 20:00 UTC. Every model run's
    prediction for a day is a sample, not only the newest."""

    def samples(self, context: LearningContext) -> Iterator[Sample]:
        start_date = context.start_date
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
            context.session, context.station_code, start_datetime, end_datetime
        )
        predicted_daily_precip = get_predicted_daily_precip(
            context.session, context.model, context.station_code, start_datetime, end_datetime
        )

        predicted_by_day = defaultdict(list)
        for predicted in predicted_daily_precip:
            predicted_by_day[predicted.prediction_timestamp].append(predicted)
        for actual in actual_daily_precip:
            y = features(actual.actual_precip_24h)
            for predicted in predicted_by_day.get(actual.day, []):
                x = features(predicted.precip_24h)
                if x is not None and y is not None:
                    yield Sample(actual.day.hour, x, y)


TEMPERATURE = HourlyVariable(
    predicted=lambda p: features(p.tmp_tgl_2), observed=lambda a: features(a.temperature)
)
RELATIVE_HUMIDITY = HourlyVariable(
    predicted=lambda p: features(p.rh_tgl_2), observed=lambda a: features(a.relative_humidity)
)
WIND_SPEED = HourlyVariable(
    predicted=lambda p: features(p.wind_tgl_10), observed=lambda a: features(a.wind_speed)
)
# Wind direction has never learned from the interpolated noon sample for 3-hourly models
# (e.g. GDPS), because its noon sample was built without wind speed. Kept as-is so this
# refactor doesn't change predictions.
WIND_DIRECTION = HourlyVariable(
    predicted=lambda p: u_v(p.wind_tgl_10, p.wdir_tgl_10),
    observed=lambda a: u_v(a.wind_speed, a.wind_direction),
    learn_from_interpolated_noon=False,
)
PRECIPITATION = DailyPrecipVariable()

BIAS_ADJUSTED_VARIABLES: tuple[BiasAdjustedVariable, ...] = (
    TEMPERATURE,
    RELATIVE_HUMIDITY,
    WIND_SPEED,
    WIND_DIRECTION,
    PRECIPITATION,
)
