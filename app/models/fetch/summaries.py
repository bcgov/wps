import datetime
import logging
from typing import List
from statistics import mean
from numpy import percentile
from geoalchemy2.shape import to_shape
from scipy.interpolate import griddata
import app.db.database
from app.db.crud import get_predictions_from_coordinates
from app.db.models import ModelRunGridSubsetPrediction, PredictionModelGridSubset, PredictionModel
from app.schemas import (
    WeatherForecastModelSummary, WeatherForecastModelSummaryValues, WeatherStation, WeatherForecastModel)
from app.models import ModelEnum
from app.wildfire_one import get_stations_by_codes
from app.models.fetch import extract_stations_in_polygon


logger = logging.getLogger(__name__)


KEYS = ('tmp_tgl_2', 'rh_tgl_2')


def _build_query_to_get_predictions(stations: List[WeatherStation], model: ModelEnum):
    """ Build a query to get the preductions for a given list of weather stations for a specified
    model.
    """
    # Using the list of stations, extract coordinates:
    coordinates = map(lambda station: [station.long, station.lat], stations)
    # Build the query:
    session = app.db.database.get_session()
    return get_predictions_from_coordinates(session, coordinates, model)


class ModelForecastSummaryBuilder():
    """ Class for generating ModelForecastSummaries """

    def __init__(self):
        """ """
        # Using the list of station codes, fetch the stations:
        self.prev_time = None
        self.prev_grid = None
        self.values = None
        self.prev_grid = None
        self.forecast_summaries = []
        self.summaries_in_grid = {}

    def init_values(self):
        self.values = {}
        for key in KEYS:
            self.values[key] = []

    def calculate_and_append_percentiles(self,
                                         summary: WeatherForecastModelSummary,
                                         timestamp: datetime.datetime,
                                         values: dict) -> None:
        """ Calculate percentiles and append.  """
        data = {'datetime': timestamp}
        for key in KEYS:
            data['{}_5th'.format(key)] = percentile(values[key], 5)
            data['{}_median'.format(key)] = mean(values[key])
            data['{}_90th'.format(key)] = percentile(values[key], 90)
        summary_value = WeatherForecastModelSummaryValues(**data)
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
                        stations: List[WeatherForecastModelSummary]) -> List:
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
            forecast_summary = WeatherForecastModelSummary(
                station=station,
                model=WeatherForecastModel(name=prediction_model.name,
                                           abbrev=prediction_model.abbreviation),
                values=[])
            self.forecast_summaries.append(forecast_summary)
            self.summaries_in_grid[station.code] = {
                'summary': forecast_summary, 'target_coordinate': [(station.long, station.lat)]}
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
            station_codes: List[int]) -> List[WeatherForecastModelSummary]:
        """ Given a model and station codes, return list of weather summaries. """

        # Get list of stations.
        stations = await get_stations_by_codes(station_codes)

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
        return self.forecast_summaries


async def fetch_model_forecast_summaries(
        model: ModelEnum,
        station_codes: List[int]) -> List[WeatherForecastModelSummary]:
    """ Given a model type (e.g. GDPS) and a  list of station codes, return a corresponding list of model
    forecast summaries containing various percentiles. """
    builder = ModelForecastSummaryBuilder()
    return await builder.get_summaries(model, station_codes)
