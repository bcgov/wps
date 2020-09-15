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
    get_most_recent_model_run_prediction)


logger = getLogger(__name__)


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
        self.temperature_model = None
        self.rh_model = None
        self.start_date = start_date
        self.end_date = end_date
        self.good_model = False

    def _collect_data(self):

        # Get hourlies (within some range)
        actuals = get_hourly_actuals(
            self.session, [self.station_code], self.start_date, self.end_date)
        # data = {
        #     'temperature': {
        #         x: [],
        #         y: []
        #     },
        #     'relative_humidity'
        # }
        x = []
        y = []
        for actual in actuals:
            # Get the most recent prediction for the actual:
            prediction = get_most_recent_model_run_prediction(
                self.session, self.model.id, self.grid, actual.weather_date)
            if prediction:
                # Interpolate spatially, to get close to our actual position:
                interpolated_value = griddata(self.points, prediction.tmp_tgl_2,
                                              self.target_coordinate, method='linear')
                # Add to the data we're going to learn from:
                # Using two variables, the interpolated temperature value, and the hour of the day.
                x.append([interpolated_value[0], actual.weather_date.hour])
                y.append(actual.temperature)

        x = np.array(x)
        y = np.array(y)
        return x, y

    def learn(self):
        self.temperature_model = LinearRegression()
        self.rh_model = LinearRegression()
        x, y = self._collect_data()
        logger.info('collected %s samples for %s', len(x), self.station_code)
        if len(x) > 0:
            # logger.info('x: %s', x)
            self.temperature_model.fit(x, y)
            r_sq = self.temperature_model.score(x, y)
            logger.info('coefficient of determination: %s', r_sq)
            self.good_model = True
        else:
            logger.info('bad model. won\'t be predicting anything.')

    def predict_temperature(self, model_temperature, timestamp):
        if self.good_model:
            return self.temperature_model.predict(
                [[model_temperature, timestamp.hour]])[0]
        return None
