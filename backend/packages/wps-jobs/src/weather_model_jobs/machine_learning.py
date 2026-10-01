"""Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.

For each station and weather model, every variable gets one linear regression per hour of the day,
trained on model predictions against observed values over the last MAX_DAYS_TO_LEARN days.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger
from typing import List, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session
from weather_model_jobs.bias_adjusted_variable import (
    BIAS_ADJUSTED_VARIABLES,
    PRECIPITATION,
    RELATIVE_HUMIDITY,
    TEMPERATURE,
    WIND_DIRECTION,
    WIND_SPEED,
    LearningContext,
    features,
    u_v,
)
from weather_model_jobs.utils.wind_direction_utils import calculate_wind_dir_from_u_v
from wps_shared.db.models.weather_models import PredictionModel

logger = getLogger(__name__)

# Number of days of historical actual data to learn from when training model.
# Experimentation has shown that about two weeks worth of data starts giving fairly good results
# compared to human forecasters.
MAX_DAYS_TO_LEARN = 19


class HourOfDayRegression:
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
        self.regressions = {variable: HourOfDayRegression() for variable in BIAS_ADJUSTED_VARIABLES}

    def learn(self):
        context = LearningContext(
            session=self.session,
            model=self.model,
            station_code=self.station_code,
            start_date=self.max_learn_date - timedelta(days=MAX_DAYS_TO_LEARN),
            end_date=self.max_learn_date,
        )
        for variable in BIAS_ADJUSTED_VARIABLES:
            regression = self.regressions[variable]
            for sample in variable.samples(context):
                regression.add(sample.hour, sample.x, sample.y)
            regression.fit()

    @staticmethod
    def _predict(
        regression: HourOfDayRegression, name: str, x: Optional[List[float]], timestamp: datetime
    ) -> Optional[np.ndarray]:
        if x is None:
            logger.warning("model %s for %s was None or NaN", name, timestamp)
            return None
        return regression.predict(timestamp.hour, x)

    def predict_temperature(self, model_temperature: float, timestamp: datetime):
        """Bias adjusted temperature for the model temperature at timestamp, or None."""
        y = self._predict(
            self.regressions[TEMPERATURE], "temperature", features(model_temperature), timestamp
        )
        return None if y is None else float(y[0])

    def predict_rh(self, model_rh: float, timestamp: datetime):
        """Bias adjusted RH for the model RH at timestamp, or None. Clamped to 0-100."""
        y = self._predict(
            self.regressions[RELATIVE_HUMIDITY], "relative humidity", features(model_rh), timestamp
        )
        return None if y is None else float(min(max(0, y[0]), 100))

    def predict_wind_speed(self, model_wind_speed: float, timestamp: datetime):
        """Bias adjusted wind speed for the model wind speed at timestamp, or None. Never negative."""
        y = self._predict(
            self.regressions[WIND_SPEED], "wind speed", features(model_wind_speed), timestamp
        )
        return None if y is None else float(max(0, y[0]))

    def predict_wind_direction(
        self, model_wind_speed: float, model_wind_dir: int, timestamp: datetime
    ):
        """Bias adjusted wind direction for the model wind speed and direction at timestamp, or None."""
        y = self._predict(
            self.regressions[WIND_DIRECTION],
            "wind speed or direction",
            u_v(model_wind_speed, model_wind_dir),
            timestamp,
        )
        return None if y is None else float(calculate_wind_dir_from_u_v(y[0], y[1]))

    def predict_precipitation(self, model_precipitation: float, timestamp: datetime):
        """Bias adjusted 24 hour precip for the model 24 hour precip at timestamp, or None. Never negative."""
        y = self._predict(
            self.regressions[PRECIPITATION],
            "precipitation",
            features(model_precipitation),
            timestamp,
        )
        return None if y is None else float(max(0, y[0]))
