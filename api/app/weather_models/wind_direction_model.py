import logging
import math
from typing import List
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import ModelRunPrediction
from app.weather_models.linear_model import LinearModel
from app.weather_models.regression_model import RegressionModelProto
from app.weather_models.wind_direction_utils import compute_u_v

logger = logging.getLogger(__name__)


def radians2degrees(radians):
    degrees = math.degrees(radians)

    if degrees < 0:
        degrees += 360.0

    return degrees


def any_none_or_nan(prediction: ModelRunPrediction, actual: HourlyActual):
    return prediction.wdir_tgl_10 is None or math.isnan(prediction.wdir_tgl_10) or\
        prediction.wind_tgl_10 is None or math.isnan(prediction.wind_tgl_10) or\
        actual.wind_direction is None or math.isnan(actual.wind_direction) or\
        actual.wind_speed is None or math.isnan(actual.wind_speed)


class WindDirectionModel(RegressionModelProto):
    """
    Wind direction regression model that decomposes degree direction into
    the u, v vectors that make it up. See: http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    for more background information.
    """

    def __init__(self):
        self._linear_model = LinearModel()

    def train(self):
        return self._linear_model.train()

    def predict(self, hour: int, model_wind_dir: List[List[int]]):
        return self._linear_model.predict(hour, model_wind_dir)

    def add_sample(self,
                   prediction: ModelRunPrediction,
                   actual: HourlyActual):
        """
        Decompose into u, v components, then add that to data sample
        """
        logger.info('adding sample for wind direction with: model_values %s, actual_value: %s',
                    prediction.wdir_tgl_10, actual.wind_direction)

        if any_none_or_nan(prediction, actual):
            # If for whatever reason we don't have an actual value, we skip this one.
            logger.warning('no actual value for wind direction: %s, or wind speed: %s',
                           actual.wind_direction, actual.wind_speed)
            return

        prediction_u_v = compute_u_v(prediction.wind_tgl_10, prediction.wdir_tgl_10)
        actual_u_v = compute_u_v(actual.wind_speed, actual.wind_direction)

        assert len(prediction_u_v) == 2
        assert len(actual_u_v) == 2
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        self._linear_model.append_x_y(prediction_u_v, actual_u_v, actual.weather_date)
