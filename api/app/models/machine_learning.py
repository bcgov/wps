""" Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata
import numpy as np
from sqlalchemy.orm import Session
from app.models import MODEL_VALUE_KEYS, construct_interpolated_noon_prediction
from app.db.models import (
    PredictionModel, PredictionModelGridSubset, ModelRunGridSubsetPrediction, HourlyActual)
from app.db.crud import get_actuals_outer_join_with_predictions


logger = getLogger(__name__)

# Corresponding key values on HourlyActual and SampleCollection
SAMPLE_VALUE_KEYS = ('temperature', 'relative_humidity')


class LinearRegressionWrapper:
    """ Class wrapping LinearRegression.
    This class just adds in a handy boolean to indicate if this linear regression model is good to use.
    """

    def __init__(self):
        self.model = LinearRegression()
        self.good_model = False  # Flag if regression model is "good" (usable).


class RegressionModels:
    """ Class for storing regression models.
    For each different reading, we have a seperate LinearRegression model.
    """

    keys = ('temperature_wrapper', 'relative_humidity_wrapper')

    def __init__(self):
        self.temperature_wrapper = LinearRegressionWrapper()
        self.relative_humidity_wrapper = LinearRegressionWrapper()


class Samples:
    """ Class for storing samples in buckets of hours.
    e.g. a temperature sample consists of an x axis (predicted values) and a y axis (observed values) put
    together in hour buckets.
    """

    def __init__(self):
        self._x = defaultdict(list)
        self._y = defaultdict(list)

    def hours(self):
        """ Return all the hours used to bucket samples together. """
        return self._x.keys()

    def append_x(self, value, timestamp: datetime):
        """ Append another predicted value. """
        self._x[timestamp.hour].append(value)

    def append_y(self, value, timestamp: datetime):
        """ Append another observered values. """
        self._y[timestamp.hour].append(value)

    def np_x(self, hour):
        """ Return numpy array of the predicted values, reshaped appropriately. """
        return np.array(self._x[hour]).reshape((-1, 1))

    def np_y(self, hour):
        """ Return a numpy array of the observed values """
        return np.array(self._y[hour])

    def add_sample(self,  # pylint: disable=too-many-arguments
                   points: List,
                   target_point: List,
                   model_values: List,
                   actual_value: float,
                   timestamp: datetime):
        """ Add a sample, interpolating the model values spatially """
        # Interpolate spatially, to get close to our actual position:
        interpolated_value = griddata(
            points, model_values, target_point, method='linear')
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        self.append_x(interpolated_value[0], timestamp)
        self.append_y(actual_value, timestamp)


class SampleCollection:
    """ Class for storing different kinds of samples """

    def __init__(self):
        self.temperature = Samples()
        self.relative_humidity = Samples()


class StationMachineLearning:  # pylint: disable=too-many-instance-attributes
    """ Wrap away machine learning in an easy to use class. """

    def __init__(self,  # pylint: disable=too-many-arguments
                 session: Session,
                 model: PredictionModel,
                 grid: PredictionModelGridSubset,
                 points: List,
                 target_coordinate: List[float],
                 station_code: int,
                 max_learn_date: datetime):
        """
        : param session: Database session.
        : param model: Prediction model, e.g. GDPS
        : param grid: Grid in which the station is contained.
        : param points: Grid represented as points.
        : param target_coordinate: Coordinate we're interested in .
        : param station_code: Code of the weather station.
        : param max_learn_date: Maximum date up to which to learn.
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

    def _add_sample_to_collection(self,
                                  prediction: ModelRunGridSubsetPrediction,
                                  actual: HourlyActual,
                                  sample_collection: SampleCollection):
        """ Take the provided prediction and observed value, adding them to the collection of samples """
        for model_key, sample_key in zip(MODEL_VALUE_KEYS, SAMPLE_VALUE_KEYS):
            model_value = getattr(prediction, model_key)
            actual_value = getattr(actual, sample_key)
            sample_value = getattr(sample_collection, sample_key)
            sample_value.add_sample(self.points, self.target_coordinate, model_value,
                                    actual_value, actual.weather_date)

    def _collect_data(self):
        """ Collect data to use for machine learning.
        """
        # Calculate the date to start learning from.
        start_date = self.max_learn_date - timedelta(days=self.max_days_to_learn)
        # Create a convenient structure to store samples in.
        sample_collection = SampleCollection()

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
                    noon_prediction = construct_interpolated_noon_prediction(prev_prediction, prediction)
                    self._add_sample_to_collection(
                        noon_prediction, prev_actual, sample_collection)

                self._add_sample_to_collection(prediction, actual, sample_collection)
                prev_prediction = prediction
            prev_actual = actual
        return sample_collection

    def learn(self):
        """ Collect data and perform linear regression.
        """
        # collect data
        data = self._collect_data()

        # iterate through the data, creating a regression model for each variable
        # and each hour.
        for sample_key, wrapper_key in zip(SAMPLE_VALUE_KEYS, RegressionModels.keys):
            sample = getattr(data, sample_key)
            for hour in sample.hours():
                regression_model = getattr(self.regression_models[hour], wrapper_key)
                regression_model.model.fit(sample.np_x(hour), sample.np_y(hour))
                # NOTE: We could get fancy here, and evaluate how good the regression actually worked,
                # how much sample data we actually had etc., and then not mark the model as being "good".
                regression_model.good_model = True

    def predict_temperature(self, model_temperature, timestamp):
        """ Predict the bias adjusted temperature for a given point in time, given a corresponding model
        temperature.
        : param model_temperature: Temperature as provided by the model
        : param timestamp: Datetime value for the predicted value.
        : return: The bias adjusted temperature as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].temperature_wrapper.good_model:
            return self.regression_models[hour].temperature_wrapper.model.predict([[model_temperature]])[0]
        return None

    def predict_rh(self, model_rh: float, timestamp: datetime):
        """ Predict the bias adjusted rh for a given point in time, given a corresponding model rh.
        : param model_rh: Relative humidity as provided by model.
        : param timestamp: Datetime value for the predicted value.
        : return: The bias adjusted RH as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].relative_humidity_wrapper.good_model:
            return self.regression_models[hour].relative_humidity_wrapper.model.predict([[model_rh]])[0]
        return None
