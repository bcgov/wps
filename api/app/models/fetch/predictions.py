""" Code for fetching data for API.
"""

import logging
from typing import List
import datetime
from datetime import timezone
from collections import defaultdict
from scipy.interpolate import griddata, interp1d
from geoalchemy2.shape import to_shape
import app.db.database
from app.schemas import (WeatherStation, WeatherModelPrediction,
                         WeatherModelPredictionValues, WeatherModelRun)
from app.db.models import ModelRunGridSubsetPrediction
import app.db.crud
import app.stations
from app.models import ModelEnum
from app.models.fetch import extract_stations_in_polygon

logger = logging.getLogger(__name__)


class MatchingStationNotFoundException(Exception):
    """ Exception raised when station cannot be found. """


class NoonInterpolator:
    """ Interpolates a noon value using a value before noon, and after noon. """

    def __init__(self):
        """ Init object. """
        # Keep track of previous values, in order to calculate missing noon value.
        self.prev_values = {}
        self.prev_timestamp = None
        self.current_values = {}
        self.current_timestamp = None
        # Noon time for all our stations, in utc, is 12PST or 20h00UTC
        self.utc_noon = datetime.time(hour=20)

    def update(self, key, value, timestamp: datetime.datetime):
        """ Update interpolater with latest value. """
        # before anything, lets translate the timestamp to utc
        utc_timestamp = timestamp.astimezone(timezone.utc)
        if self.current_timestamp != utc_timestamp:
            # Swap out current with previous
            self.prev_timestamp = self.current_timestamp
            self.prev_values = self.current_values
            # Reset current
            self.current_values = {}
            self.current_timestamp = utc_timestamp

        self.current_values[key] = value

    def is_before_noon(self, timestamp: datetime.datetime):
        """ Return true if given time is before utc noon """
        return timestamp.time() < self.utc_noon

    def is_after_noon(self, timestamp: datetime.datetime):
        """ Retrun true if given time is after uct noon """
        return timestamp.time() > self.utc_noon

    def calculate_noon_value(self) -> WeatherModelPredictionValues:
        """ Calcualte the interpolated noon value (if possible) """
        # If the previous timestamp was before noon, and the current timestamp is after noon,
        # it means there is no noon value, and we can interpolate one.
        result = None
        if (self.prev_timestamp and
                self.is_before_noon(self.prev_timestamp) and
                self.is_after_noon(self.current_timestamp)):
            noon = datetime.datetime(year=self.prev_timestamp.year, month=self.prev_timestamp.month,
                                     day=self.prev_timestamp.day, hour=self.utc_noon.hour,
                                     minute=self.utc_noon.minute, tzinfo=timezone.utc)
            result = WeatherModelPredictionValues(datetime=noon)
            # x-axis is the timestamp
            x_axis = (self.prev_timestamp.timestamp(),
                      self.current_timestamp.timestamp())
            # for each key value, we have a y-axis
            y_axis = {}
            for key, value in self.prev_values.items():
                y_axis[key] = [value, self.current_values[key]]
            for key, value in y_axis.items():
                function = interp1d(x_axis, value, kind='linear')
                interpolated_value = function(noon.timestamp())
                # the interpolated value is in the form of an array, we just want the 1st element.
                setattr(result, key, interpolated_value.item(0))
        return result


def _add_model_prediction_record_to_prediction_schema(prediction_schema: WeatherModelPrediction,
                                                      prediction_record: ModelRunGridSubsetPrediction,
                                                      points: List[float],
                                                      noon_interpolator: NoonInterpolator):
    """ Add the model prediction for a particular timestamp to the prediction schema. """
    prediction_values = WeatherModelPredictionValues(
        datetime=prediction_record.prediction_timestamp)
    target_coordinate = [(prediction_schema.station.long,
                          prediction_schema.station.lat)]
    key_map = {
        'tmp_tgl_2': 'temperature',
        'rh_tgl_2': 'relative_humidity'
    }

    # Iterate through each of the mappings.
    for key, target in key_map.items():
        # Get the values.
        values = getattr(prediction_record, key)
        if values:
            # If there are values, calculate the interpolated value, and set.
            interpolated_value = griddata(
                points, values, target_coordinate, method='linear')[0]
            setattr(prediction_values, target, interpolated_value)
            noon_interpolator.update(
                target, interpolated_value, prediction_record.prediction_timestamp)

    noon_value = noon_interpolator.calculate_noon_value()
    if noon_value:
        prediction_schema.values.append(noon_value)
    prediction_schema.values.append(prediction_values)


def _fetch_model_predictions_by_stations(
        session,
        model: ModelEnum,
        stations: List[WeatherStation]) -> List[WeatherModelPrediction]:
    """ Fetch predictions for stations. """
    # pylint: disable=too-many-locals
    # Get the most recent model run:
    most_recent_run = app.db.crud.get_most_recent_model_run(
        session, model, app.db.crud.LATLON_15X_15)
    logger.info(
        'most recent run: {0.prediction_run_timestamp}'.format(most_recent_run))
    # Get the predictions:
    query = app.db.crud.get_model_run_predictions(
        session, most_recent_run, map(lambda station: [station.long, station.lat], stations))

    # Construct response object:
    model_run = WeatherModelRun(
        datetime=most_recent_run.prediction_run_timestamp,
        name=most_recent_run.prediction_model.name,
        abbreviation=most_recent_run.prediction_model.abbreviation,
        projection=most_recent_run.prediction_model.projection)

    predictions = []
    tmp_station_list = stations.copy()
    prev_grid = None
    points = None
    stations_in_polygon = None
    predictions_in_grid = {}

    for grid, prediction_record in query:
        if grid != prev_grid:
            prev_grid = grid
            predictions_in_grid = {}
            # Get the bounding points (ignore the last point of the polygon)
            poly = to_shape(grid.geom)
            points = list(poly.exterior.coords)[:-1]
            stations_in_polygon = extract_stations_in_polygon(
                tmp_station_list, poly)
            # Initialize predictions for all the stations in this grid.
            for station in stations_in_polygon:
                prediction = WeatherModelPrediction(
                    station=station, model_run=model_run, values=[])
                predictions.append(prediction)
                predictions_in_grid[station.code] = prediction, NoonInterpolator(
                )
                # pop the station off the list
                tmp_station_list.remove(station)

        # It could conceivably happen that we have N where N>1 stations in a
        # grid, in which case we need to iterate over the grid predictions N times.
        for prediction, noon_interpolator in predictions_in_grid.values():
            _add_model_prediction_record_to_prediction_schema(
                prediction, prediction_record, points, noon_interpolator)
        # NOTE: The code would be much simpler if we only did the interpolation afterwards.

    return predictions


async def _fetch_model_predictions_by_station_codes(model: ModelEnum, station_codes: List[int]):
    """ Fetch predictions from database.
    """
    # Using the list of station codes, fetch the stations:
    stations = await app.stations.get_stations_by_codes(station_codes)
    session = app.db.database.get_session()
    # Fetch the all the predictions.
    predictions = _fetch_model_predictions_by_stations(
        session, model, stations)

    return predictions


async def fetch_model_predictions(model: ModelEnum, station_codes: List[int]):
    """ Fetch model weather predictions for a given list of stations and a given model. """
    # Fetch predictions from the database.
    return await _fetch_model_predictions_by_station_codes(model, station_codes)


async def _fetch_most_recent_historic_predictions_by_station_codes(model: ModelEnum, station_codes: List[int]) -> List[WeatherModelPrediction]:
    """ Fetch the most recent historic model predictions from database based on each station's coordinates. """
    # construct temporary helper dictionary of relevant weather stations
    stations_dict = defaultdict(list)
    stations = await app.stations.get_stations_by_codes(station_codes)
    for station in stations:
        stations_dict[station.code] = station

    # construct helper dictionary of WeatherModelPredictions
    # weather_model_predictions_dict is indexed by station_code, then by prediction_timestamp
    weather_model_predictions_dict = defaultdict(lambda: defaultdict(list))

    # send the query
    session = app.db.database.get_session()
    historic_predictions = app.db.crud.get_most_recent_historic_station_model_predictions(
        session, station_codes, model)
    for prediction in historic_predictions:
        # construct the WeatherModelPredictionValue
        prediction_value = WeatherModelPredictionValues(
            temperature=prediction.WeatherStationModelPrediction.tmp_tgl_2,
            relative_humidity=prediction.WeatherStationModelPrediction.rh_tgl_2,
            datetime=prediction.WeatherStationModelPrediction.prediction_timestamp
        )

        existing_prediction = weather_model_predictions_dict[prediction.WeatherStationModelPrediction.station_code][
            prediction.WeatherStationModelPrediction.prediction_timestamp]
        # check if a WeatherModelPrediction already exists in weather_model_predictions_dict for the station_code and prediction_timestamp
        if(existing_prediction != []):
            if(existing_prediction.model_run.datetime > prediction.PredictionModelRunTimestamp.prediction_run_timestamp):
                continue
        else:
            model_run = WeatherModelRun(
                datetime=prediction.PredictionModelRunTimestamp.prediction_run_timestamp,
                name=prediction.PredictionModel.name,
                abbreviation=model,
                projection=prediction.PredictionModel.projection
            )
            # construct the WeatherModelPrediction
            weather_model_prediction = WeatherModelPrediction(
                station=stations_dict[prediction.WeatherStationModelPrediction.station_code],
                model_run=model_run,
                values=[prediction_value]
            )
            weather_model_predictions_dict[prediction.WeatherStationModelPrediction.station_code][
                prediction.WeatherStationModelPrediction.prediction_timestamp] = weather_model_prediction

    # flatten the nested dict into a regular list of WeatherModelPredictions
    weather_predictions_response = [item for timestamp in list(
        weather_model_predictions_dict.values()) for item in list(timestamp.values())]

    return weather_predictions_response


async def fetch_most_recent_historic_predictions(model: ModelEnum, station_codes: List[int]):
    """ Fetch most recently issued model prediction for the last 5 days for a given list of stations and a given model. """
    return await _fetch_most_recent_historic_predictions_by_station_codes(model, station_codes)
