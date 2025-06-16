import logging
import math
from typing import List, Optional
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction
from wps_jobs.weather_model_jobs.utils.interpolate import (
    construct_interpolated_noon_prediction,
)
from wps_jobs.weather_model_jobs.utils.linear_model import LinearModel
from wps_jobs.weather_model_jobs.utils.precip_model import PrecipModel
from wps_jobs.weather_model_jobs.utils.regression_model import (
    RegressionModelProto,
    model_2_actual_keys,
)
from wps_jobs.weather_model_jobs.utils.sample import Samples
from wps_jobs.weather_model_jobs.utils.utils import (
    construct_dictionary_from_list_by_property,
)
from wps_jobs.weather_model_jobs.utils.wind_direction_model import WindDirectionModel

logger = logging.getLogger(__name__)


class RegressionModelsV2:
    """Class for storing regression models.
    TODO: migrate other models to this once wind direction is verified
    """

    def __init__(self):
        self._model_keys: List[str] = list(model_2_actual_keys.keys())
        self._models: List[RegressionModelProto] = [
            WindDirectionModel(linear_model=LinearModel(samples=Samples()))
        ]
        self._precip_model: RegressionModelProto = PrecipModel(
            linear_model=LinearModel(samples=Samples())
        )

    def add_samples(self, prediction: ModelRunPrediction, actual: HourlyActual):
        for model in self._models:
            model.add_sample(prediction, actual)

    def add_precip_samples(self, actual_values, predicted_values):
        predicted_values_dict = construct_dictionary_from_list_by_property(
            predicted_values, "prediction_timestamp"
        )
        for actual in actual_values:
            daily_actual = actual.actual_precip_24h
            timestamp = actual.day
            daily_predicted_list = predicted_values_dict.get(timestamp)
            if daily_predicted_list is None:
                continue
            for daily_predicted in daily_predicted_list:
                precip_24h = daily_predicted.precip_24h
                if (
                    daily_actual is not None
                    and not math.isnan(daily_actual)
                    and precip_24h is not None
                    and not math.isnan(precip_24h)
                ):
                    self._precip_model.add_sample(
                        daily_actual, daily_predicted.precip_24h, timestamp
                    )

    def collect_data(self, data: list[tuple[HourlyActual, Optional[ModelRunPrediction]]]):
        # We need to keep track of previous so that we can do interpolation for the global model.
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
                    # If there's a gap in the data (like with the GLOBAL model) - then make up
                    # a noon prediction using interpolation, and add it as a sample.
                    noon_prediction = construct_interpolated_noon_prediction(
                        prev_prediction, prediction, self._model_keys
                    )
                    self.add_samples(noon_prediction, prev_actual)

                self.add_samples(prediction, actual)
                prev_prediction = prediction
            prev_actual = actual

    def train(self):
        # iterate through the data, creating a regression model for each variable
        # and each hour.
        for model in self._models:
            model.train()

    def train_precip(self):
        self._precip_model.train()
