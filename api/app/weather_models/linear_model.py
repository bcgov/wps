import logging
from datetime import datetime
from typing import List
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LinearRegression
from collections import defaultdict
from app.weather_models.sample import Samples

logger = logging.getLogger(__name__)


class LinearModel():
    _models: defaultdict[int, LinearRegression]
    _samples: Samples

    def __init__(self):
        self._models = defaultdict(LinearRegression)
        self._samples = Samples()

    def append_x_y(self, prediction_value: List[float], actual_value: List[float], timestamp: datetime):
        self._samples.append_x(prediction_value, timestamp)
        self._samples.append_y(actual_value, timestamp)

    def append_x(self, value, timestamp: datetime):
        self._samples.append_x(value, timestamp)

    def append_y(self, value, timestamp: datetime):
        self._samples.append_y(value, timestamp)

    def train(self):
        for hour in self._samples.hours():
            try:
                self._models[hour].fit(self._samples.np_x(hour), self._samples.np_y(hour))
            except ValueError as e:
                logger.info(e)

    def predict(self, hour: int, model_wind_dir: List[List[int]]):
        try:
            prediction = self._models[hour].predict(model_wind_dir)
            logger.info("Predicted wind dir for model: %s, hour: %s, prediction: %s", self._key, hour, prediction)
            return prediction[0]
        except NotFittedError as _:
            return None
