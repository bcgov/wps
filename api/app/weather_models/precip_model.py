import logging
import math
from datetime import datetime
from typing import List
from app.weather_models.linear_model import LinearModel
from app.weather_models.regression_model import RegressionModelBase

logger = logging.getLogger(__name__)

class PrecipModel(RegressionModelBase):
    """
    24 hour accumulated precipitation regression model.
    """

    def __init__(self, linear_model: LinearModel):
        self._linear_model = linear_model

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

