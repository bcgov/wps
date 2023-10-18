import logging
from collections import defaultdict
from typing import List
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LinearRegression
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models.regression_model import RegressionModelProto
from app.weather_models.sample import Samples

logger = logging.getLogger(__name__)


class WindDirectionModel(RegressionModelProto):
    """ 
    Wind direction regression model that decomposes degree direction into
    the u, v vectors that make it up. See: http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    for more background information.
    """

    def __init__(self, model_key: str):
        self._key = model_key
        self._models = defaultdict(LinearRegression)
        self._samples = Samples()

    def add_sample(self,
                   prediction: ModelRunPrediction,
                   actual: HourlyActual):
        """
        Decompose into u, v components, then add that to data sample
        """

        pass

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
