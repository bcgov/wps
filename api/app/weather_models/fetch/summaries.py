""" Weather Model Summaries
"""
import datetime
import logging
from typing import List, Union
from numpy import percentile
import app.stations
from app.weather_models import ModelEnum
from app.schemas.weather_models import (
    WeatherModelPredictionSummary,
    WeatherModelPredictionSummaryValues,
    WeatherPredictionModel)
import app.time_utils as time_utils
import app.db.database
from app.db.crud.weather_models import get_station_model_predictions_order_by_prediction_timestamp
from app.db.models import PredictionModel, WeatherStationModelPrediction


logger = logging.getLogger(__name__)


KEYS = ('tmp_tgl_2', 'rh_tgl_2')


def _build_query_to_get_predictions(
        station_codes: List[int],
        model: ModelEnum) -> List[Union[WeatherStationModelPrediction, PredictionModel]]:
    """ Build a query to get the predictions for a given list of weather stations for a specified
    model.
    """
    # Build the query:
    session = app.db.database.get_read_session()
    # We are only interested in the last 5 days.
    now = time_utils.get_utc_now()
    back_5_days = now - datetime.timedelta(days=5)
    return get_station_model_predictions_order_by_prediction_timestamp(
        session, station_codes, model, back_5_days, now)


class ModelPredictionSummaryBuilder():
    """ Class for generating ModelPredictionSummaries """

    def __init__(self):
        """ Prepare class. """
        self.prev_time = None
        self.prev_station = None
        self.values = None
        self.prediction_summaries = []
        self.prediction_summary = None
        self.stations: dict = None

    def init_values(self):
        """ Initialize values. """
        self.values = {}
        for key in KEYS:
            self.values[key] = []

    def calculate_and_append_percentiles(self,
                                         timestamp: datetime.datetime,
                                         values: dict) -> None:
        """ Calculate percentiles and append.  """
        data = {'datetime': timestamp}
        for key in KEYS:
            data['{}_5th'.format(key)] = percentile(values[key], 5)
            data['{}_median'.format(key)] = percentile(values[key], 50)
            data['{}_90th'.format(key)] = percentile(values[key], 90)
        summary_value = WeatherModelPredictionSummaryValues(**data)
        self.prediction_summary.values.append(summary_value)

    def calculate_summaries(self, prev_time):
        """ Calculate and append percentiles if present """
        if self.values:
            self.calculate_and_append_percentiles(self.prev_time, self.values)
        self.prev_time = prev_time
        self.values = None

    def handle_new_station(self,
                           prediction: WeatherStationModelPrediction,
                           prediction_model: PredictionModel):
        """ When a new station is detected, we need to:
        -) calculate percentiles for accumulated values.
        -) prepare a summary for the new station.
        """
        self.prev_station = prediction.station_code
        station = self.stations[prediction.station_code]
        self.prediction_summary = WeatherModelPredictionSummary(
            station=station,
            model=WeatherPredictionModel(name=prediction_model.name,
                                         abbrev=prediction_model.abbreviation),
            values=[])
        self.prediction_summaries.append(self.prediction_summary)

    def accumulate_values(self, prediction: WeatherStationModelPrediction):
        """ As we iterate through predictions, we accumulate the values so that we can calculate
        the percentiles. """
        for key in KEYS:
            # Get the values.
            key_value = getattr(prediction, key)
            if key_value:
                if not self.values:
                    self.init_values()
                self.values[key].append(key_value)

    async def get_summaries(
            self,
            model: ModelEnum,
            station_codes: List[int]) -> List[WeatherModelPredictionSummary]:
        """ Given a model and station codes, return list of weather summaries. """
        # Get list of stations.
        self.stations = {
            station.code: station for station in await
            app.stations.get_stations_by_codes(station_codes)}

        # Build database query
        new_query = _build_query_to_get_predictions(station_codes, model)

        # Iterate through the result of our query.
        for prediction, prediction_model in new_query:
            if prediction.station_code != self.prev_station:
                # when the station changes, we need to process accumulated values and
                # create new responses for the new station.
                first_station = self.prev_station is None
                if not first_station:
                    # Before moving on, we need to finish calculating the values for the previous station.
                    self.calculate_summaries(prediction.prediction_timestamp)
                self.handle_new_station(prediction, prediction_model)
                # Set prev_time (so that we don't trigger calculate_summaries)
                self.prev_time = prediction.prediction_timestamp
            elif self.prev_time != prediction.prediction_timestamp:
                # The timestamp has changed, process the accumulated values:
                self.calculate_summaries(prediction.prediction_timestamp)

            # Accumulate the values (to be process at next station change, time change, or when done):
            self.accumulate_values(prediction)

        self.calculate_summaries(None)
        return self.prediction_summaries


async def fetch_model_prediction_summaries(
        model: ModelEnum,
        station_codes: List[int]) -> List[WeatherModelPredictionSummary]:
    """ Given a model type (e.g. GDPS) and a  list of station codes, return a corresponding list of model
    prediction summaries containing various percentiles. """
    builder = ModelPredictionSummaryBuilder()
    return await builder.get_summaries(model, station_codes)
