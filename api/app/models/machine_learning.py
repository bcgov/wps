from datetime import datetime
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata
import numpy as np
from app.db.models import PredictionModel, PredictionModelGridSubset
from app.db.crud import (
    get_hourly_actuals,
    get_weather_station_model_prediction,
    get_actuals_paired_with_predictions,
    get_most_recent_model_run_prediction)


logger = getLogger(__name__)


def calc_rh_hour(timestamp):
    """
    20h00 UTC is solar noon in BC.
    22h00 UTC is 14h00 in BC.
    For some reason I don't understand there's correlation here.
    """
    return abs(((timestamp.hour + 2) % 24) - 12)


def calc_temp_hour(timestamp):
    """
    20h00 is solar noon in BC. (20h00 utc, -8 is 12 pacific, noon)
    8 hours after noon, is 20h00 PST, or 04h00 UTC
    for some reason, we get the highest temperature score if we make this the midpoint.
    I don't understand.
    """
    return abs(((timestamp.hour + 8) % 24) - 12)


class ModelWrapper:

    model = LinearRegression()
    good = False


class DataAxisWrapper:
    x = []
    y = []

    def np_x(self):
        return np.array(self.x)

    def np_y(self):
        return np.array(self.y)


class DataWrapper:
    temperature = DataAxisWrapper()
    rh = DataAxisWrapper()


class RegressionModels:

    temperature = ModelWrapper()
    rh = ModelWrapper()


class StationMachineLearning:

    def __init__(self,
                 session,
                 model: PredictionModel,
                 grid: PredictionModelGridSubset,
                 points: List,
                 target_coordinate: List,
                 station_code: int,
                 start_date: datetime,
                 end_date: datetime):
        """
        :param station_code: 
        :param start_date: date to start learning.
        :param end_date: date to end learning.
        """
        self.session = session
        self.model = model
        self.grid = grid
        self.points = points
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.regression_models = RegressionModels()
        self.start_date = start_date
        self.end_date = end_date
        self.good_model = False

    def _add_sample(self, points, target_point, model_values, actual_value, timestamp, target, hour_function):
        # Interpolate spatially, to get close to our actual position:
        interpolated_value = griddata(
            points, model_values, target_point, method='linear')
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        target.x.append([interpolated_value[0], hour_function(timestamp)])
        target.y.append(actual_value)

    def _collect_data(self):

        # Get hourlies (within some range)
        # logger.info('fetching hourly actuals...')
        actuals = get_hourly_actuals(
            self.session, [self.station_code], self.start_date, self.end_date)
        # logger.info('done fetching hourly actuals.')

        data = DataWrapper()
        # logger.info('iterating through actuals...')
        query = get_actuals_paired_with_predictions(
            self.session, self.model.id, self.grid.id, self.station_code, self.start_date, self.end_date)
        prev_actual = None
        for actual, prediction in query:
            if prev_actual != actual:
                self._add_sample(self.points, self.target_coordinate, prediction.tmp_tgl_2,
                                 actual.temperature, actual.weather_date, data.temperature, calc_temp_hour)
                self._add_sample(self.points, self.target_coordinate, prediction.rh_tgl_2,
                                 actual.relative_humidity, actual.weather_date, data.rh, calc_rh_hour)
        # logger.info('done iterating through actuals.')
        return data

    def learn(self):
        # logger.info('collecting data...')
        data = self._collect_data()
        # logger.info('collected %s samples for %s', len(x), self.station_code)
        if len(data.temperature.x) > 3:
            # using a REALLY low tolerance for number of samples - this can cause issues!
            # logger.info('x: %s', x)
            # logger.info('y: %s', y)
            self.regression_models.temperature.model.fit(
                data.temperature.np_x(), data.temperature.np_y())
            self.regression_models.rh.model.fit(
                data.rh.np_x(), data.rh.np_y())
            # r_sq = self.regression_models.temperature.model.score(x, y)
            # logger.info('coefficient of determination: %s', r_sq)
            # could look at r_sq to decide if the model is good enough
            self.regression_models.temperature.good = True
            self.regression_models.rh.good = True
        else:
            logger.debug('bad model. won\'t be predicting anything.')

    def predict_temperature(self, model_temperature, timestamp):
        if self.regression_models.temperature.good:
            return self.regression_models.temperature.model.predict(
                [[model_temperature, calc_temp_hour(timestamp)]])[0]
        return None

    def predict_rh(self, model_rh, timestamp):
        if self.regression_models.rh.good:
            return self.regression_models.rh.model.predict([[model_rh, calc_rh_hour(timestamp)]])[0]
