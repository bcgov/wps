import logging
from typing import List
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models import construct_interpolated_noon_prediction
from app.weather_models.linear_model import LinearModel
from app.weather_models.regression_model import RegressionModelProto, model_2_actual_keys
from app.weather_models.wind_direction_model import WindDirectionModel

logger = logging.getLogger(__name__)


class RegressionModelsV2:
    """ Class for storing regression models.
    TODO: migrate other models to this once wind direction is verified
    """

    def __init__(self):
        self._model_keys: List[str] = list(model_2_actual_keys.keys())
        self._models: List[RegressionModelProto] = [
            WindDirectionModel(linear_model=LinearModel())
        ]

    def add_samples(self, prediction: ModelRunPrediction, actual: HourlyActual):
        for model in self._models:
            model.add_sample(prediction, actual)

    def collect_data(self, query):
        # We need to keep track of previous so that we can do interpolation for the global model.
        prev_actual = None
        prev_prediction = None
        for actual, prediction in query:
            if prev_actual != actual and prediction is not None:
                if (prev_actual is not None
                        and prev_prediction is not None
                        and prev_actual.weather_date.hour == 20
                        and prediction.prediction_timestamp.hour == 21
                        and prev_prediction.prediction_timestamp.hour == 18):
                    # If there's a gap in the data (like with the GLOBAL model) - then make up
                    # a noon prediction using interpolation, and add it as a sample.
                    noon_prediction = construct_interpolated_noon_prediction(
                        prev_prediction, prediction, self._model_keys)
                    self.add_samples(noon_prediction, prev_actual)

                self.add_samples(prediction, actual)
                prev_prediction = prediction
            prev_actual = actual

    def train(self):
        # iterate through the data, creating a regression model for each variable
        # and each hour.
        for model in self._models:
            model.train()
