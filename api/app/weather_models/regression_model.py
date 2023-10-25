import logging
import math
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Protocol
from collections import defaultdict
from abc import abstractmethod
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models.linear_model import LinearModel
from app.weather_models.sample import Samples

logger = logging.getLogger(__name__)

# maps weather orm model keys to actual weather orm model keys
model_2_actual_keys: Dict[str, str] = {
    ModelRunPrediction.tmp_tgl_2.name: HourlyActual.temperature.name,  # Not used yet, just for tests
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

    def __init__(self, model_key: str, linear_model: LinearModel):
        self._key = model_key
        self._linear_model = linear_model

    def train(self):
        return self._linear_model.train()

    def predict(self, hour: int, model_wind_dir: List[List[int]]):
        return self._linear_model.predict(hour, model_wind_dir)

    def add_sample(self,
                   prediction: ModelRunPrediction,
                   actual: HourlyActual):
        """ Add a sample, with prediction as an x value, actual as a y value """

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

            self._linear_model.append_x_y(model_value, actual_value, actual.weather_date)
