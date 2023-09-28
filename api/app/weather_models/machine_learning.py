""" Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
import numpy as np
from sqlalchemy.orm import Session
from app.weather_models import SCALAR_MODEL_VALUE_KEYS, construct_interpolated_noon_prediction
from app.db.models.weather_models import (PredictionModel, ModelRunPrediction)
from app.db.models.observations import HourlyActual
from app.db.crud.observations import get_actuals_left_outer_join_with_predictions


logger = getLogger(__name__)

# Corresponding key values on HourlyActual and SampleCollection
SAMPLE_VALUE_KEYS = ('temperature', 'relative_humidity', 'wind_speed', 'wind_direction')
# Number of days of historical actual data to learn from when training model
MAX_DAYS_TO_LEARN = 19


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

    keys = ('temperature_wrapper', 'relative_humidity_wrapper',
            'wind_speed_wrapper', 'wind_direction_wrapper')

    def __init__(self):
        self.temperature_wrapper = LinearRegressionWrapper()
        self.relative_humidity_wrapper = LinearRegressionWrapper()
        self.wind_speed_wrapper = LinearRegressionWrapper()
        self.wind_direction_wrapper = LinearRegressionWrapper()


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

    def add_sample(self,
                   model_value: float,
                   actual_value: float,
                   timestamp: datetime,
                   model_key: str,
                   sample_key: str):
        """ Add a sample, interpolating the model values spatially """
        # Additional logging to assist with finding errors:
        logger.info('adding sample for %s->%s with: model_values %s, actual_value: %s',
                    model_key, sample_key, model_value, actual_value)
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        self.append_x(model_value, timestamp)
        self.append_y(actual_value, timestamp)


class SampleCollection:
    """ Class for storing different kinds of samples """

    def __init__(self):
        self.temperature = Samples()
        self.relative_humidity = Samples()
        self.wind_speed = Samples()
        self.wind_direction = Samples()


class StationMachineLearning:
    """ Wrap away machine learning in an easy to use class. """

    def __init__(self,
                 session: Session,
                 model: PredictionModel,
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
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.regression_models = defaultdict(RegressionModels)
        self.max_learn_date = max_learn_date
        # Maximum number of days to try to learn from. Experimentation has shown that
        # about two weeks worth of data starts giving fairly good results compared to human forecasters.
        # NOTE: This could be an environment variable.
        self.max_days_to_learn = MAX_DAYS_TO_LEARN

    def _add_sample_to_collection(self,
                                  prediction: ModelRunPrediction,
                                  actual: HourlyActual,
                                  sample_collection: SampleCollection):
        """ Take the provided prediction and observed value, adding them to the collection of samples """
        for model_key, sample_key in zip(SCALAR_MODEL_VALUE_KEYS, SAMPLE_VALUE_KEYS):
            model_value = getattr(prediction, model_key)
            if model_value is not None:
                actual_value = getattr(actual, sample_key)
                if actual_value is None or np.isnan(actual_value):
                    # If for whatever reason we don't have an actual value, we skip this one.
                    logger.warning('no actual value for %s', sample_key)
                    continue
                sample_value = getattr(sample_collection, sample_key)
                sample_value.add_sample(model_value, actual_value, actual.weather_date, model_key, sample_key)
            else:
                # Sometimes, for reasons that probably need investigation, model values
                # are None.
                logger.warning('no model value for %s->%s', model_key, sample_key)

    def _collect_data(self):
        """ Collect data to use for machine learning.
        """
        # Calculate the date to start learning from.
        start_date = self.max_learn_date - \
            timedelta(days=self.max_days_to_learn)
        # Create a convenient structure to store samples in.
        sample_collection = SampleCollection()

        # Query actuals, with prediction left outer joined (so if there isn't a prediction, you'll
        # get an actual, but prediction will be None)
        query = get_actuals_left_outer_join_with_predictions(
            self.session, self.model.id, self.station_code, start_date, self.max_learn_date)
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

                self._add_sample_to_collection(
                    prediction, actual, sample_collection)
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
                regression_model = getattr(
                    self.regression_models[hour], wrapper_key)
                regression_model.model.fit(
                    sample.np_x(hour), sample.np_y(hour))
                # NOTE: We could get fancy here, and evaluate how good the regression actually worked,
                # how much sample data we actually had etc., and then not mark the model as being "good".
                regression_model.good_model = True

    def predict_temperature(self, model_temperature: float, timestamp: datetime):
        """ Predict the bias adjusted temperature for a given point in time, given a corresponding model
        temperature.
        : param model_temperature: Temperature as provided by the model
        : param timestamp: Datetime value for the predicted value.
        : return: The bias adjusted temperature as predicted by the linear regression model.
        """
        if model_temperature is None:
            logger.warning('model temperature for %s was None', timestamp)
            return None
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
        if self.regression_models[hour].relative_humidity_wrapper.good_model and model_rh is not None:
            predicted_rh = self.regression_models[hour].relative_humidity_wrapper.model.predict([[model_rh]])[0]
            # in the real world the RH value can't be negative. Sometimes linear regression returns negative value, so assume 0
            return max(0, predicted_rh)
        return None

    def predict_wind_speed(self, model_wind_speed: float, timestamp: datetime):
        """ Predict the bias-adjusted wind speed for a given point in time, given a corresponding model wind speed.
        : param model_wind_speed: Wind speed as provided by the model
        : param timestamp: Datetime value for the predicted value
        : return: The bias adjusted wind speed as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].wind_speed_wrapper.good_model and model_wind_speed is not None:
            predicted_wind_speed = self.regression_models[hour].wind_speed_wrapper.model.predict([[model_wind_speed]])[
                0]
            # in the real world the wind speed can't be negative. Sometimes linear regression returns negative value, so assume 0
            return max(0, predicted_wind_speed)
        return None

    def predict_wind_direction(self, model_wind_dir: int, timestamp: datetime):
        """ Predict the bias-adjusted wind direction for a given point in time, given a corresponding model wind direction.
        : param model_wind_dir: Wind direction as provided by the model
        : param timestamp: Datetime value for the predicted value
        : return: The bias-adjusted wind direction as predicted by the linear regression model.
        """
        hour = timestamp.hour
        if self.regression_models[hour].wind_direction_wrapper.good_model and model_wind_dir is not None:
            predicted_wind_dir = self.regression_models[hour].wind_direction_wrapper.model.predict([[model_wind_dir]])[
                0]
            # a valid wind direction value is between 0 and 360. If the returned value is outside these bounds, correct it
            return predicted_wind_dir % 360
        return None
