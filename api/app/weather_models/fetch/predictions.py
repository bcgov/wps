""" Code for fetching data for API.
"""

import logging
from typing import List
import datetime
from datetime import timezone
from collections import defaultdict
from scipy.interpolate import griddata, interp1d
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
import app.db.database
from app.schemas.weather_models import (WeatherModelPrediction,
                                        WeatherModelPredictionValues, WeatherModelRun,
                                        ModelRunPredictions,
                                        WeatherStationModelRunsPredictions)
from app.schemas.stations import WeatherStation
from app.db.models import ModelRunGridSubsetPrediction, WeatherStationModelPrediction
from app.db.crud.weather_models import (get_station_model_predictions,
                                        get_station_model_prediction_from_previous_model_run)
import app.stations
from app.weather_models import ModelEnum, ProjectionEnum
from app.weather_models.fetch import extract_stations_in_polygon
from app.tests import dump_sqlalchemy_response_to_json

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
        'rh_tgl_2': 'relative_humidity',
        'apcp_sfc_0': 'total_precipitation'
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
        projection: ProjectionEnum,
        stations: List[WeatherStation]) -> List[WeatherModelPrediction]:
    """ Fetch predictions for stations. """
    # pylint: disable=too-many-locals
    # Get the most recent model run:
    most_recent_run = app.db.crud.weather_models.get_most_recent_model_run(
        session, model, projection)
    logger.info(
        'most recent run: %s', most_recent_run.prediction_run_timestamp)
    # Get the predictions:
    query = app.db.crud.weather_models.get_model_run_predictions(
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


async def _fetch_model_predictions_by_station_codes(
        model: ModelEnum,
        projection: ProjectionEnum,
        station_codes: List[int]):
    """ Fetch predictions from database.
    """
    # Using the list of station codes, fetch the stations:
    stations = await app.stations.get_stations_by_codes(station_codes)
    session = app.db.database.get_read_session()
    # Fetch the all the predictions.
    predictions = _fetch_model_predictions_by_stations(
        session, model, projection, stations)

    return predictions


async def fetch_model_predictions(model: ModelEnum, projection: ProjectionEnum, station_codes: List[int]):
    """ Fetch model weather predictions for a given list of stations and a given model. """
    # Fetch predictions from the database.
    return await _fetch_model_predictions_by_station_codes(model, projection, station_codes)


def _fetch_delta_precip_for_prev_model_run(
        session: Session,
        model: ModelEnum,
        prediction: WeatherStationModelPrediction,
        prev_station_predictions: dict,
        prediction_model_run_timestamp: datetime.datetime):
    # Look if we can find the previous value in memory
    if prediction.prediction_timestamp in prev_station_predictions[prediction.station_code]:
        return prev_station_predictions[prediction.station_code][prediction.prediction_timestamp]['prediction'].delta_precipitation
    # Uh oh - couldn't find it - let's go look in the database.
    # This should only happen in extreme edge cases!
    prev_prediction = get_station_model_prediction_from_previous_model_run(
        session, prediction.station_code, model, prediction.prediction_timestamp, prediction_model_run_timestamp)
    if prev_prediction:
        return prev_prediction.delta_precip
    return None


async def fetch_model_run_predictions_by_station_code(
        model: ModelEnum,
        station_codes: List[int],
        end_date: datetime) -> List[WeatherStationModelRunsPredictions]:
    """ Fetch model predictions from database based on list of station code, up to the specified end_date.
    Predictions are grouped by station and model run.
    """
    # We're only interested in the last 5 days.
    five_days_ago = app.time_utils.get_utc_now() - datetime.timedelta(days=5)
    # send the query (ordered by prediction date.)
    session = app.db.database.get_read_session()
    historic_predictions = get_station_model_predictions(
        session, station_codes, model, five_days_ago, end_date)

    # Helper dictionary.
    station_predictions = defaultdict(dict)

    # NOTE: The query could be optimized to only return the latest predictions.
    for prediction, prediction_model_run_timestamp, prediction_model in historic_predictions:
        # If this is true, it means that we are at hour 000 of the model run but not at the 0th hour of the
        # day, so we need to look at the accumulated precip from the previous model run to calculate the
        # delta_precip
        precip_value = None
        if prediction.prediction_timestamp == prediction_model_run_timestamp.prediction_run_timestamp and \
                prediction.prediction_timestamp.hour > 0:
            precip_value = _fetch_delta_precip_for_prev_model_run(
                session,
                model,
                prediction,
                station_predictions,
                prediction_model_run_timestamp.prediction_run_timestamp)
        # This condition catches situations where we are not at hour 000 of the model run, or where it is
        # hour 000 but there was nothing returned from _fetch_delta_precip_for_prev_model_run()
        if precip_value is None:
            precip_value = prediction.delta_precip
        station_predictions[prediction.station_code][prediction.prediction_timestamp] = {
            'model_run': WeatherModelRun(
                datetime=prediction_model_run_timestamp.prediction_run_timestamp,
                name=prediction_model.name,
                abbreviation=model,
                projection=prediction_model.projection
            ),
            'prediction': WeatherModelPredictionValues(
                temperature=prediction.tmp_tgl_2,
                bias_adjusted_temperature=prediction.bias_adjusted_temperature,
                relative_humidity=prediction.rh_tgl_2,
                bias_adjusted_relative_humidity=prediction.bias_adjusted_rh,
                delta_precipitation=precip_value,
                datetime=prediction.prediction_timestamp
            )
        }

    # Re-structure the data, grouping data by station and model run.
    # NOTE: It means looping through twice, but the code reads easier this way.
    stations = {station.code: station for station in await app.stations.get_stations_by_codes(station_codes)}
    response = []
    for station_code, predictions in station_predictions.items():
        model_run_dict = {}
        for prediction in predictions.values():

            if prediction['model_run'].datetime in model_run_dict:
                model_run_predictions = model_run_dict[prediction['model_run'].datetime]
            else:
                model_run_predictions = ModelRunPredictions(
                    model_run=prediction['model_run'],
                    values=[]
                )
                model_run_dict[prediction['model_run'].datetime] = model_run_predictions
            model_run_predictions.values.append(prediction['prediction'])

        response.append(WeatherStationModelRunsPredictions(
            station=stations[station_code],
            model_runs=list(model_run_dict.values())
        ))

    return response
