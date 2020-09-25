""" Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata
import numpy as np
from sqlalchemy.orm import Session
from app.models import interpolate_between_two_points
from app.db.models import PredictionModel, PredictionModelGridSubset, ModelRunGridSubsetPrediction
from app.db.crud import get_actuals_outer_join_with_predictions


logger = getLogger(__name__)


class ModelWrapper:

    def __init__(self):
        self.model = LinearRegression()
        self.good = False


@dataclass
class DataAxisWrapper:

    def __init__(self):
        self._x = defaultdict(list)
        self._y = defaultdict(list)

    def keys(self):
        return self._x.keys()

    def append_x(self, value, timestamp: datetime):
        self._x[timestamp.hour].append(value)

    def append_y(self, value, timestamp: datetime):
        self._y[timestamp.hour].append(value)

    def np_x(self, hour):
        return np.array(self._x[hour]).reshape((-1, 1))

    def np_y(self, hour):
        return np.array(self._y[hour])


@dataclass
class Data:
    """ Class for storing samples """
    temperature: DataAxisWrapper
    relative_humidity: DataAxisWrapper

    def __init__(self):
        self.temperature = DataAxisWrapper()
        self.relative_humidity = DataAxisWrapper()


class RegressionModels:

    def __init__(self):
        self.temperature = ModelWrapper()
        self.rh = ModelWrapper()


def _construct_noon_prediction(prediction_a: ModelRunGridSubsetPrediction,
                               prediction_b: ModelRunGridSubsetPrediction):
    """ Construct a noon prediction by interpolating.
    """
    # create a noon prediction.
    noon_prediction = ModelRunGridSubsetPrediction()
    noon_prediction.prediction_timestamp = prediction_a.prediction_timestamp.replace(
        hour=20)
    # throw timestamps into their own variables.
    timestamp_a = prediction_a.prediction_timestamp.timestamp()
    timestamp_b = prediction_b.prediction_timestamp.timestamp()
    noon_timestamp = noon_prediction.prediction_timestamp.timestamp()
    # calculate interpolated values.
    for key in ('tmp_tgl_2', 'rh_tgl_2'):
        value = interpolate_between_two_points(
            timestamp_a, timestamp_b, getattr(prediction_a, key),
            getattr(prediction_b, key), noon_timestamp)
        setattr(noon_prediction, key, value)
    return noon_prediction


class StationMachineLearning:
    """ Wrap away machine learning in an easy to use class. """

    def __init__(self,
                 session: Session,
                 model: PredictionModel,
                 grid: PredictionModelGridSubset,
                 points: List,
                 target_coordinate: List[float],
                 station_code: int,
                 max_learn_date: datetime):
        """
        :param session: Database session.
        :param model: Prediction model, e.g. GDPS
        :param grid: Grid in which the station is contained.
        :param points: Grid represented as points.
        :param target_coordinate: Coordinate we're interested in.
        :param station_code: Code of the weather station.
        :param max_learn_date: Maximum date up to which to learn.
        """
        self.session = session
        self.model = model
        self.grid = grid
        self.points = points
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.regression_models = defaultdict(RegressionModels)
        self.max_learn_date = max_learn_date
        # Maximum number of days to try to learn from. Experimentation has shown that
        # about two weeks worth of data starts giving fairly good results compared to human forecasters.
        # NOTE: This could be an environment variable.
        self.max_days_to_learn = 19

    def _add_sample(self, points, target_point, model_values, actual_value, timestamp, target):
        # Interpolate spatially, to get close to our actual position:
        interpolated_value = griddata(
            points, model_values, target_point, method='linear')
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        target.append_x(interpolated_value[0], timestamp)
        target.append_y(actual_value, timestamp)

    def _add_prediction_to_sample(self, prediction, actual, data):
        self._add_sample(self.points, self.target_coordinate, prediction.tmp_tgl_2,
                         actual.temperature, actual.weather_date, data.temperature)
        self._add_sample(self.points, self.target_coordinate, prediction.rh_tgl_2,
                         actual.relative_humidity, actual.weather_date, data.rh)

    def _collect_data(self):
        """ Collect date to use for machine learning.
        """
        # Calculate the date to start learning from.
        start_date = self.max_learn_date - timedelta(days=self.max_days_to_learn)

        data = Data()

        # Query actuals, with prediction outer joined (so if there's no prediction, it will be None)
        query = get_actuals_outer_join_with_predictions(
            self.session, self.model.id, self.grid.id, self.station_code, start_date, self.max_learn_date)
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
                    noon_prediction = _construct_noon_prediction(prev_prediction, prediction)
                    self._add_prediction_to_sample(
                        noon_prediction, prev_actual, data)

                self._add_prediction_to_sample(prediction, actual, data)
                prev_prediction = prediction
            prev_actual = actual
        return data

    def learn(self):
        """ Collect data and perform linear regression.
        """
        data = self._collect_data()

        for hour in data.temperature.keys():
            self.regression_models[hour].temperature.model.fit(
                data.temperature.np_x(hour), data.temperature.np_y(hour)
            )
            self.regression_models[hour].temperature.good = True
        for hour in data.relative_humidity.keys():
            self.regression_models[hour].rh.model.fit(
                data.relative_humidity.np_x(hour), data.relative_humidity.np_y(hour)
            )
            self.regression_models[hour].rh.good = True

    def predict_temperature(self, model_temperature, timestamp):
        """ Predict the bias adjusted temperature for a given point in time, given a corresponding model
        temperature.
        :param model_temperature: Temperature as provided by the model
        :param timestamp: Datetime value for the predicted value.
        :return: The bias adjusted temperature as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].temperature.good:
            return self.regression_models[hour].temperature.model.predict([[model_temperature]])[0]
        return None

    def predict_rh(self, model_rh: float, timestamp: datetime):
        """ Predict the bias adjusted rh for a given point in time, given a corresponding model rh.
        :param model_rh: Relative humidity as provided by model.
        :param timestamp: Datetime value for the predicted value.
        :return: The bias adjusted RH as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].rh.good:
            return self.regression_models[hour].rh.model.predict([[model_rh]])[0]
        return None
