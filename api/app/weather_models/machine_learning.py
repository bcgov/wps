""" Module for calculating the bias for a weather station use basic Machine Learning through Linear
Regression.
"""
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from typing import List
from logging import getLogger
from sklearn.linear_model import LinearRegression
import numpy as np
from sqlalchemy.orm import Session
from app.weather_models import SCALAR_MODEL_VALUE_KEYS, construct_interpolated_noon_prediction
from app.db.models.weather_models import (PredictionModel, ModelRunPrediction)
from app.db.models.observations import HourlyActual
from app.db.crud.observations import (get_accumulated_precip_by_24h_interval,
                                      get_actuals_left_outer_join_with_predictions,
                                      get_predicted_daily_precip)
from app.weather_models.sample import Samples
from app.weather_models.weather_models import RegressionModelsV2
from app.weather_models.wind_direction_model import compute_u_v
from app.weather_models.wind_direction_utils import calculate_wind_dir_from_u_v


logger = getLogger(__name__)

# Corresponding key values on HourlyActual and SampleCollection
SAMPLE_VALUE_KEYS = ('temperature', 'relative_humidity', 'wind_speed')
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
            'wind_speed_wrapper')

    def __init__(self):
        self.temperature_wrapper = LinearRegressionWrapper()
        self.relative_humidity_wrapper = LinearRegressionWrapper()
        self.wind_speed_wrapper = LinearRegressionWrapper()


class SampleCollection:
    """ Class for storing different kinds of samples """

    def __init__(self):
        self.temperature = Samples()
        self.relative_humidity = Samples()
        self.wind_speed = Samples()


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
        : param target_coordinate: Coordinate we're interested in .
        : param station_code: Code of the weather station.
        : param max_learn_date: Maximum date up to which to learn.
        """
        self.session = session
        self.model = model
        self.target_coordinate = target_coordinate
        self.station_code = station_code
        self.regression_models = defaultdict(RegressionModels)
        self.regression_models_v2 = RegressionModelsV2()
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

    def _collect_data(self, start_date: datetime):
        """ Collect data to use for machine learning.
        """
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
                    noon_prediction = construct_interpolated_noon_prediction(
                        prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS)
                    self._add_sample_to_collection(
                        noon_prediction, prev_actual, sample_collection)

                self._add_sample_to_collection(
                    prediction, actual, sample_collection)
                prev_prediction = prediction
            prev_actual = actual
        return sample_collection
    
    def learn(self):
        # Calculate the date to start learning from.
        start_date =  self.max_learn_date - \
            timedelta(days=self.max_days_to_learn)
        self.learn_models(start_date)
        self.learn_precip_model(start_date)

    def learn_models(self, start_date: datetime):
        """ Collect data and perform linear regression.
        """
        # collect data
        data = self._collect_data(start_date)

        # iterate through the data, creating a regression model for each variable
        # and each hour.
        for sample_key, wrapper_key in zip(SAMPLE_VALUE_KEYS, RegressionModels.keys):
            sample = getattr(data, sample_key)
            for hour in sample.hours():
                regression_model = getattr(
                    self.regression_models[hour], wrapper_key)
                regression_model.model.fit(
                    sample.np_x(hour).reshape(-1, 1), sample.np_y(hour))
                # NOTE: We could get fancy here, and evaluate how good the regression actually worked,
                # how much sample data we actually had etc., and then not mark the model as being "good".
                regression_model.good_model = True

        # wdir specific using new structure for regression handling
        query = get_actuals_left_outer_join_with_predictions(
            self.session, self.model.id, self.station_code, start_date, self.max_learn_date)
        self.regression_models_v2.collect_data(query)
        self.regression_models_v2.train()
        
    def learn_precip_model(self, start_date):
        """ Collect precip data and perform linear regression.
        """
        # Precip is based on 24 hour periods at 20:00 hours UTC. Use the start_date
        # parameter to calculate a start_datetime for the same date but at 20:00 UTC.
        start_datetime = datetime(start_date.year, start_date.month, start_date.day, 20, tzinfo=timezone.utc)
        # The end datetime is yesterday at 20:00 UTC.
        end_date = date.today() - timedelta(days=-1)
        end_datetime = datetime(end_date.year, end_date.month, end_date.day, 20, tzinfo=timezone.utc)
        # Get the actual precip values
        actual_daily_precip = get_accumulated_precip_by_24h_interval(
            self.session, self.station_code, start_datetime, end_datetime)
        # Get the model predicted values
        predicted_daily_precip = get_predicted_daily_precip(
            self.session, self.model, self.station_code, start_datetime, end_datetime)
        self.regression_models_v2.add_precip_samples(actual_daily_precip, predicted_daily_precip)
        self.regression_models_v2.train_precip()

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

    def predict_wind_direction(self, model_wind_speed: float, model_wind_dir: int, timestamp: datetime):
        """ Predict the bias-adjusted wind direction for a given point in time, given a corresponding model wind direction.
        : param model_wind_speed: Wind speed as provided by the model
        : param model_wind_dir: Wind direction as provided by the model
        : param timestamp: Datetime value for the predicted value
        : return: The bias-adjusted wind direction as predicted by the linear regression model.
        """
        hour = timestamp.hour
        u_v = compute_u_v(model_wind_speed, model_wind_dir)
        predicted_wind_dir = self.regression_models_v2._models[0].predict(hour, [u_v])
        logger.info("Predicted wind direction: %s for value: %s at hour: %s", predicted_wind_dir, model_wind_dir, hour)
        if predicted_wind_dir is None or u_v is None:
            return None

        assert len(predicted_wind_dir) == 2
        predicted_wind_dir_deg = calculate_wind_dir_from_u_v(u_v[0], u_v[1])
        return predicted_wind_dir_deg
    
    def predict_precipitation(self, model_precipitation: float, timestamp: datetime):
        """ Predict the 24 hour precipitation for a given point in time, given a
        corresponding model precipitation.
        : param model_precipitation: Precipitation as provided by the model
        : param timestamp: Datetime value for the predicted value.
        : return: The bias adjusted 24 hour precipitation as predicted by the linear regression model.
        """
        if model_precipitation is None:
            logger.warning('model precipitation for %s was None', timestamp)
            return None
        hour = timestamp.hour
        predicted_precip_24h = self.regression_models_v2._precip_model.predict(hour, [[model_precipitation]])
        if predicted_precip_24h is None or len(predicted_precip_24h) == 0:
            return None
        return max(0, predicted_precip_24h[0])
