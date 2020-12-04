""" Weather Model Summaries
"""
import datetime
import logging
from typing import List, Union
from numpy import percentile
from geoalchemy2.shape import to_shape
from scipy.interpolate import griddata
from app.weather_models.fetch import extract_stations_in_polygon
import app.stations
from app.weather_models import ModelEnum
from app.schemas.stations import WeatherStation
from app.schemas.weather_models import (
    WeatherModelPredictionSummary,
    WeatherModelPredictionSummaryValues,
    WeatherPredictionModel)
import app.time_utils as time_utils
import app.db.database
from app.db.crud.weather_models import get_predictions_from_coordinates, get_station_model_predictions
from app.db.models import (ModelRunGridSubsetPrediction, PredictionModelGridSubset, PredictionModel,
                           WeatherStationModelPrediction, PredictionModelRunTimestamp)


logger = logging.getLogger(__name__)


KEYS = ('tmp_tgl_2', 'rh_tgl_2')


def _build_query_to_get_predictions_new(
        station_codes: List[int],
        model: ModelEnum) -> List[Union[WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel]]:
    """ Build a query to get the predictions for a given list of weather stations for a specified
    model.
    """
    # Build the query:
    session = app.db.database.get_read_session()
    # We are only interested in the last 5 days.
    now = time_utils.get_utc_now()
    back_5_days = now - datetime.timedelta(days=5)
    return get_station_model_predictions(session, station_codes, model, back_5_days, now)


def _build_query_to_get_predictions(stations: List[WeatherStation], model: ModelEnum):
    """ Build a query to get the predictions for a given list of weather stations for a specified
    model.
    """
    # Using the list of stations, extract coordinates:
    coordinates = map(lambda station: [station.long, station.lat], stations)
    # Build the query:
    session = app.db.database.get_read_session()
    return get_predictions_from_coordinates(session, coordinates, model)


class NewModelPredictionSummaryBuilder():

    def __init__(self):
        """ Prepare class. """
        self.prev_station = None
        self.prev_time = None
        self.prediction_summaries = []
        self.prediction_summary = None
        self.stations = None
        self.values = None

    def init_values(self):
        """ Initialize values. """
        self.values = {}
        for key in KEYS:
            self.values[key] = []

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
        # TODO: make this a common function
        self.stations = {
            station.code: station for station in await
            app.stations.get_stations_by_codes(station_codes)}

        # Build database query
        new_query = _build_query_to_get_predictions_new(station_codes, model)

        # Iterate through the result of our query.
        for prediction, model_run, prediction_model in new_query:
            # Check for station change - when the station changes, we need to process accumulated values and
            # create new responses for the new station.
            if prediction.station_code != self.prev_station:
                self.handle_new_station(prediction, prediction_model)

            # Check time change - when the time changes, we need to process the accumulated values:
            if self.prev_time != prediction.prediction_timestamp:
                # The timestamp has changed, process the accumulated values:
                self.calculate_summaries(prediction.prediction_timestamp)

            # Accumulate the values (to be process at next station change, time change,
            # or when done iterating):
            self.accumulate_values(prediction)

        self.calculate_summaries(None)
        return self.prediction_summaries


class ModelPredictionSummaryBuilder():
    """ Class for generating ModelPredictionSummaries """

    def __init__(self):
        """ Prepare class. """
        self.prev_time = None
        self.prev_grid = None
        self.values = None
        self.prediction_summaries = []
        self.summaries_in_grid = {}
        self.most_recent_historic = {}

    def init_values(self):
        """ Initialize values. """
        self.values = {}
        for key in KEYS:
            self.values[key] = []

    def calculate_and_append_percentiles(self,
                                         summary: WeatherModelPredictionSummary,
                                         timestamp: datetime.datetime,
                                         values: dict) -> None:
        """ Calculate percentiles and append.  """
        data = {'datetime': timestamp}
        for key in KEYS:
            data['{}_5th'.format(key)] = percentile(values[key], 5)
            data['{}_median'.format(key)] = percentile(values[key], 50)
            data['{}_90th'.format(key)] = percentile(values[key], 90)
        summary_value = WeatherModelPredictionSummaryValues(**data)
        summary.values.append(summary_value)

    def calculate_summaries(self, prev_time):
        """ Calculate and append percentiles if present """
        if self.values:
            for summary in self.summaries_in_grid.values():
                self.calculate_and_append_percentiles(
                    summary['summary'], self.prev_time, self.values)
        self.prev_time = prev_time
        self.values = None

    def handle_new_grid(self,
                        grid: PredictionModelGridSubset,
                        prediction_model: PredictionModel,
                        stations: List[WeatherStation]) -> List:
        """ When a new grid is detected, we need to:
        -) calculate percentiles for accumulated values.
        -) calculate bounding points, to be used in interpolation.
        -) prepare a summary for each station in the grid.
        """
        # The grid has changed, process the accumulated values:
        self.calculate_summaries(self.prev_time)
        self.prev_grid = grid
        self.summaries_in_grid = {}
        # Get the bounding points (ignore the last point of the polygon)
        poly = to_shape(grid.geom)
        points = list(poly.exterior.coords)[:-1]
        stations_in_polygon = extract_stations_in_polygon(
            stations, poly)
        for station in stations_in_polygon:
            prediction_summary = WeatherModelPredictionSummary(
                station=station,
                model=WeatherPredictionModel(name=prediction_model.name,
                                             abbrev=prediction_model.abbreviation),
                values=[])
            self.prediction_summaries.append(prediction_summary)
            self.summaries_in_grid[station.code] = {
                'summary': prediction_summary, 'target_coordinate': [(station.long, station.lat)]}
            stations.remove(station)
        return points

    def accumulate_values(self, prediction: ModelRunGridSubsetPrediction, grid_points: List):
        """ As we iterate through predictions, we accumulate the values so that we can calculate
        the percentiles. """
        for summary in self.summaries_in_grid.values():
            for key in KEYS:
                # Get the values.
                key_values = getattr(prediction, key)
                if key_values:
                    # If there are values, calculate the interpolated value, and set.
                    interpolated_value = griddata(
                        grid_points, key_values, summary['target_coordinate'], method='linear')[0]
                    if not self.values:
                        self.init_values()
                    self.values[key].append(interpolated_value)

    async def get_summaries(
            self,
            model: ModelEnum,
            station_codes: List[int]) -> List[WeatherModelPredictionSummary]:
        """ Given a model and station codes, return list of weather summaries. """
        # Get list of stations.
        stations = await app.stations.get_stations_by_codes(station_codes)

        # Build database query
        query = _build_query_to_get_predictions(stations, model)

        # Iterate through the result of our query.
        for grid, prediction, prediction_model in query:
            # Check for grid change - when the grid changes, we need to process accumulated values and
            # create new responses for that stations in those grids.
            if grid != self.prev_grid:
                grid_points = self.handle_new_grid(
                    grid, prediction_model, stations)

            # Check time change - when the time changes, we need to process the accumulated values:
            if self.prev_time != prediction.prediction_timestamp:
                # The timestamp has changed, process the accumulated values:
                self.calculate_summaries(prediction.prediction_timestamp)

            # Accumulate the values (to be process at next grid change, time change, or when done iterating):
            self.accumulate_values(prediction, grid_points)

        # We're done iterating through all records, so we process the last accumulated values:
        self.calculate_summaries(None)
        return self.prediction_summaries


async def fetch_model_prediction_summaries(
        model: ModelEnum,
        station_codes: List[int]) -> List[WeatherModelPredictionSummary]:
    """ Given a model type (e.g. GDPS) and a  list of station codes, return a corresponding list of model
    prediction summaries containing various percentiles. """
    # old_builder = ModelPredictionSummaryBuilder()
    # old_result = await old_builder.get_summaries(model, station_codes)

    new_builder = NewModelPredictionSummaryBuilder()
    new_result = await new_builder.get_summaries(model, station_codes)

    return new_result
