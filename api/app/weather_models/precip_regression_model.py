import logging
import math
from datetime import datetime
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LinearRegression
from typing import List
from collections import defaultdict
from app.weather_models.utils import construct_dictionary_from_list_by_property
from app.weather_models.sample import Samples

logger = logging.getLogger(__name__)


class PrecipRegressionModel:
    """
    Class to manage a regression dataset for precipitation
    """

    def __init__(self):
        self._models = defaultdict(LinearRegression)
        self._samples = Samples()

    def train(self):
        for hour in self._samples.hours():
            self._models[hour].fit(self._samples.np_x(hour), self._samples.np_y(hour))
            self._is_fitted = True

    def get_model_at_hour(self, hour: int):
        return self._models[hour]

    def predict(self, hour: int, model_value: List[List[int]]):
        try:
            prediction = self._models[hour].predict(model_value)
            logger.info("Predicted precip for model: %s, hour: %s, prediction: %s", "precip", hour, prediction)
            return prediction[0]
        except NotFittedError as _:
            return None

    def add_sample(self, actual_value: float, model_value: float, timestamp: datetime):
        if actual_value is None:
            logger.warning('no actual value for model key: "precip"')
            return
        if model_value is None:
            logger.warning('no model value for model key: "precip"')
            return
        # Add to the data we're going to learn from:
        # Using two variables, the actual or modelled precip value, and the hour of the day.
        self._samples.append_x(model_value, timestamp)
        self._samples.append_y(actual_value, timestamp)

    def add_samples(self, actual_values, predicted_values):
        predicted_values_dict = construct_dictionary_from_list_by_property(predicted_values, "prediction_timestamp")
        for actual in actual_values:
            daily_actual = actual.actual_precip_24h
            timestamp = actual.day
            daily_predicted_list = predicted_values_dict.get(timestamp)
            if daily_predicted_list is None:
                continue
            for daily_predicted in daily_predicted_list:
                precip_24h = daily_predicted.precip_24h
                if daily_actual is not None and not math.isnan(daily_actual) and precip_24h is not None and not math.isnan(precip_24h):
                    self.add_sample(daily_actual, daily_predicted.precip_24h, timestamp)
