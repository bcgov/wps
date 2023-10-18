import logging
import math
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Protocol
from collections import defaultdict
from abc import abstractmethod
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models import construct_interpolated_noon_prediction
from app.weather_models.sample import Samples

logger = logging.getLogger(__name__)

# maps weather orm model keys to actual weather orm model keys
model_2_actual_keys: Dict[str, str] = {
    ModelRunPrediction.wdir_tgl_10.name: HourlyActual.wind_direction.name
}


class RegressionModelProto(Protocol):
    _key: str
    _models: defaultdict[int, LinearRegression]
    _samples: Samples

    @abstractmethod
    def add_sample(self,
                   prediction: ModelRunPrediction,
                   actual: HourlyActual): raise NotImplementedError

    @abstractmethod
    def train(self): raise NotImplementedError

    @abstractmethod
    def predict(self, hour: int, model_wind_dir: List[List[int]]): raise NotImplementedError


class RegressionModel(RegressionModelProto):
    """ 
    Default class to manage a regression dataset
    """

    def __init__(self, model_key: str):
        self._key = model_key
        self._models = defaultdict(LinearRegression)
        self._samples = Samples()

    def train(self):
        for hour in self._samples.hours():
            self._models[hour].fit(self._samples.np_x(hour), self._samples.np_y(hour))

    def predict(self, hour: int, model_wind_dir: List[List[int]]):
        try:
            prediction = self._models[hour].predict(model_wind_dir)
            logger.info("Predicted wind dir for model: %s, hour: %s, prediction: %s", self._key, hour, prediction)
            return prediction[0]
        except NotFittedError as _:
            return None

    def add_sample(self,
                   prediction: ModelRunPrediction,
                   actual: HourlyActual):
        """ Add a sample, interpolating the model values spatially """

        model_value = getattr(prediction, self._key)
        actual_value = getattr(actual, model_2_actual_keys[self._key])

        logger.info('adding sample for %s->%s with: model_values %s, actual_value: %s',
                    self._key, self._key, model_value, actual_value)

        if model_value is not None:
            if actual_value is None or math.isnan(actual_value):
                # If for whatever reason we don't have an actual value, we skip this one.
                logger.warning('no actual value for model key: %s, actual key: %s',
                               self._key, model_2_actual_keys[self._key])
                return

            # Add to the data we're going to learn from:
            # Using two variables, the interpolated temperature value, and the hour of the day.
            self._samples.append_x(model_value, actual.weather_date)
            self._samples.append_y(actual_value, actual.weather_date)


class RegressionModelsV2:
    """ Class for storing regression models.
    TODO: migrate other models to this once wind direction is verified
    """

    def __init__(self):
        self._model_keys: List[str] = list(model_2_actual_keys.keys())
        self._models: List[RegressionModelProto] = [
            RegressionModel(model_key=ModelRunPrediction.wdir_tgl_10.name)
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
