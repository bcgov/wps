import logging
import math
from datetime import datetime
from typing import List
from app.weather_models.linear_model import LinearModel
from app.weather_models.utils import construct_dictionary_from_list_by_property

logger = logging.getLogger(__name__)

class PrecipModel():
    """
    24 hour accumulated precipitation regression model.
    """

    def __init__(self, linear_model: LinearModel):
        self._linear_model = linear_model

    def train(self):
        return self._linear_model.train()

    def predict(self, hour: int, model_precip: List[List[int]]):
        return self._linear_model.predict(hour, model_precip)

    def add_sample(self, actual_value: float, model_value: float, timestamp: datetime):
        if actual_value is None:
            logger.warning('no actual value for model key: "precip"')
            return
        if model_value is None:
            logger.warning('no model value for model key: "precip"')
            return
        # Add to the data we're going to learn from:
        # Using two variables, the actual or modelled precip value, and the hour of the day.
        self._linear_model.append_x_y([model_value], [actual_value], timestamp)

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
