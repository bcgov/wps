from datetime import datetime, timedelta
from collections import defaultdict
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata, interp1d
import numpy as np
from app.db.models import PredictionModel, PredictionModelGridSubset, ModelRunGridSubsetPrediction
from app.db.crud import (
    get_hourly_actuals,
    get_weather_station_model_prediction,
    get_actuals_outer_join_with_predictions,
    get_most_recent_model_run_prediction,
    get_predictions)


logger = getLogger(__name__)


def interpolate(x_axis, before, after, timestamp):
    y_axis = [
        [before[0], after[0]],
        [before[1], after[1]],
        [before[2], after[2]],
        [before[3], after[3]]
    ]
    return interp1d(x_axis, y_axis, kind='linear')(timestamp)


class ModelWrapper:

    def __init__(self):
        self.model = LinearRegression()
        self.good = False


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


class DataWrapper:

    def __init__(self):
        self.temperature = DataAxisWrapper()
        self.rh = DataAxisWrapper()


class RegressionModels:

    def __init__(self):
        self.temperature = ModelWrapper()
        self.rh = ModelWrapper()


class StationMachineLearning:

    def __init__(self,
                 session,
                 model: PredictionModel,
                 grid: PredictionModelGridSubset,
                 points: List,
                 target_coordinate: List,
                 station_code: int,
                 max_learn_date: datetime):
        """
        :param station_code:
        :param max_learn_date: maximum date up to wich to learn.
        """
        self.session = session
        self.model = model
        self.grid = grid
        self.points = points
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.regression_models = defaultdict(RegressionModels)
        self.max_learn_date = max_learn_date
        self.good_model = False
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
        start_date = self.max_learn_date - \
            timedelta(days=self.max_days_to_learn)

        data = DataWrapper()

        query = get_actuals_outer_join_with_predictions(
            self.session, self.model.id, self.grid.id, self.station_code, start_date, self.max_learn_date)
        prev_actual = None
        prev_prediction = None
        for actual, prediction in query:
            if prev_actual != actual and prediction is not None:
                if (prev_actual is not None
                        and prev_prediction is not None
                        and prev_actual.weather_date.hour == 20
                        and prediction.prediction_timestamp.hour == 21
                        and prev_prediction.prediction_timestamp.hour == 18):
                    noon_prediction = ModelRunGridSubsetPrediction()
                    noon_prediction.prediction_timestamp = prediction.prediction_timestamp.replace(
                        hour=20)
                    # x-axis is the timestamp
                    x_axis = (prev_prediction.prediction_timestamp.timestamp(),
                              prediction.prediction_timestamp.timestamp())
                    # calculate interpolated values
                    noon_prediction.tmp_tgl_2 = interpolate(
                        x_axis, prev_prediction.tmp_tgl_2,
                        prediction.tmp_tgl_2,
                        noon_prediction.prediction_timestamp.timestamp())
                    noon_prediction.rh_tgl_2 = interpolate(
                        x_axis, prev_prediction.rh_tgl_2,
                        prediction.rh_tgl_2,
                        noon_prediction.prediction_timestamp.timestamp())
                    self._add_prediction_to_sample(
                        noon_prediction, prev_actual, data)

                self._add_prediction_to_sample(prediction, actual, data)
                prev_prediction = prediction
            prev_actual = actual
        return data

    def learn(self):
        data = self._collect_data()

        for hour in data.temperature.keys():
            self.regression_models[hour].temperature.model.fit(
                data.temperature.np_x(hour), data.temperature.np_y(hour)
            )
            self.regression_models[hour].temperature.good = True
        for hour in data.rh.keys():
            self.regression_models[hour].rh.model.fit(
                data.rh.np_x(hour), data.rh.np_y(hour)
            )
            self.regression_models[hour].rh.good = True

    def predict_temperature(self, model_temperature, timestamp):
        hour = timestamp.hour
        if self.regression_models[hour].temperature.good:
            return self.regression_models[hour].temperature.model.predict([[model_temperature]])[0]
        return None

    def predict_rh(self, model_rh, timestamp):
        hour = timestamp.hour
        if self.regression_models[hour].rh.good:
            return self.regression_models[hour].rh.model.predict([[model_rh]])[0]
