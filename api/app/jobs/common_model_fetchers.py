import os
import sys
import datetime
from typing import Generator, List
from urllib.parse import urlparse
import logging
import tempfile
import requests
import numpy
from pyproj import Geod
from scipy.interpolate import griddata
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from app.db.crud.weather_models import (get_processed_file_record,
                                        get_processed_file_count,
                                        get_prediction_model_run_timestamp_records,
                                        get_model_run_predictions_for_grid,
                                        get_grids_for_coordinate,
                                        get_weather_station_model_prediction,
                                        delete_model_run_grid_subset_predictions,
                                        get_prediction_model,
                                        get_prediction_run,
                                        update_prediction_run)
from app.weather_models.machine_learning import StationMachineLearning
from app.weather_models import ModelEnum, ProjectionEnum, construct_interpolated_noon_prediction
from app.schemas.stations import WeatherStation
from app import config, configure_logging
import app.utils.time as time_utils
from app.utils.redis import create_redis
from app.stations import get_stations_synchronously
from app.weather_models.process_grib import GribFileProcessor, ModelRunInfo
from app.db.models import (ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           WeatherStationModelPrediction, ModelRunGridSubsetPrediction)
import app.db.database
from app.rocketchat_notifications import send_rocketchat_notification

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


class UnhandledPredictionModelType(Exception):
    """ Exception raised when an unknown model type is encountered. """


class CompletedWithSomeExceptions(Exception):
    """ Exception raised when processing completed, but there were some non critical exceptions """


def download(url: str, path: str, config_cache_var: str, config_cache_expiry_var=None) -> str:
    """
    Download a file from a url.
    NOTE: was using wget library initially, but has the drawback of not being able to control where the
    temporary files are stored. This is problematic, as giving the application write access to /app
    is a security concern.
    TODO: Would be nice to make this an async
    """
    # Infer filename from url.
    filename = os.path.split(url)[-1]
    # Construct target location for downloaded file.
    target = os.path.join(os.getcwd(), path, filename)
    # Get the file.
    # We don't strictly need to use redis - but it helps a lot when debugging on a local machine, it
    # saves having to re-download the file all the time.
    # It also save a lot of bandwidth in our dev environment, where we have multiple workers downloading
    # the same files over and over.
    if config.get(config_cache_var) == 'True':
        cache = create_redis()
        try:
            cached_object = cache.get(url)
        except Exception as error:  # pylint: disable=broad-except
            cached_object = None
            logger.error(error)
    else:
        cached_object = None
        cache = None
    if cached_object:
        logger.info('Cache hit %s', url)
        # Store the cached object in a file
        with open(target, 'wb') as file_object:
            # Write the file.
            file_object.write(cached_object)
    else:
        logger.info('Downloading %s', url)
        # It's important to have a timeout on the get, otherwise the call may get stuck for an indefinite
        # amount of time - there is no default value for timeout. During testing, it was observed that
        # downloads usually complete in less than a second.
        response = requests.get(url, timeout=60)
        # If the response is 200/OK.
        if response.status_code == 200:
            # Store the response.
            with open(target, 'wb') as file_object:
                # Write the file.
                file_object.write(response.content)
            # Cache the response
            if cache:
                with open(target, 'rb') as file_object:
                    # Cache for 6 hours (21600 seconds)
                    cache.set(url, file_object.read(), ex=config.get(config_cache_expiry_var, 21600))
        elif response.status_code == 404:
            # We expect this to happen frequently - just log for info.
            logger.info('404 error for %s', url)
            target = None
        else:
            # Raise an exception
            response.raise_for_status()
        # Return file location.
    return target


def get_closest_index(coordinate: List, points: List):
    """ Get the index of the point closest to the coordinate """
    # https://pyproj4.github.io/pyproj/stable/api/geod.html
    # Use GRS80 ellipsoid (it's what NAD83 uses)
    geod = Geod(ellps="GRS80")
    # Calculate the distance each point is from the coordinate.
    _, _, distances = geod.inv([coordinate[0] for _ in range(4)],
                               [coordinate[1] for _ in range(4)],
                               [x[0] for x in points],
                               [x[1] for x in points])
    # Return the index of the point with the shortest distance.
    return numpy.argmin(distances)


def flag_file_as_processed(url: str, session: Session):
    """ Flag the file as processed in the database """
    processed_file = get_processed_file_record(session, url)
    if processed_file:
        logger.info('re-procesed %s', url)
    else:
        logger.info('file processed %s', url)
        processed_file = ProcessedModelRunUrl(
            url=url,
            create_date=time_utils.get_utc_now())
    processed_file.update_date = time_utils.get_utc_now()
    # pylint: disable=no-member
    session.add(processed_file)
    session.commit()


def check_if_model_run_complete(session: Session, urls):
    """ Check if a particular model run is complete """
    # pylint: disable=no-member
    actual_count = get_processed_file_count(session, urls)
    expected_count = len(urls)
    logger.info('we have processed %s/%s files',
                actual_count, expected_count)
    return actual_count == expected_count


def apply_data_retention_policy():
    """
    We can't keep data forever, we just don't have the space.
    """
    with app.db.database.get_write_session_scope() as session:
        # The easiest target, is the 4 points surrounding a weather station, once it's interpolated
        # and used for machine learning - it's no longer of use.
        # It would be great to keep it forever. we could go back and use historic data to improve
        # machine learning, but unfortunately takes a lot of space.
        # Currently we're using 19 days of data for machine learning, so
        # keeping 21 days (3 weeks) of historic data is sufficient.
        oldest_to_keep = time_utils.get_utc_now() - datetime.timedelta(days=21)
        delete_model_run_grid_subset_predictions(session, oldest_to_keep)


class ModelValueProcessor:
    """ Iterate through model runs that have completed, and calculate the interpolated weather predictions.
    """

    def __init__(self, session):
        """ Prepare variables we're going to use throughout """
        self.session = session
        self.stations = get_stations_synchronously()
        self.station_count = len(self.stations)

    def _process_model_run(self, model_run: PredictionModelRunTimestamp):
        """ Interpolate predictions in the provided model run for all stations. """
        logger.info('Interpolating values for model run: %s', model_run)
        # Iterate through stations.
        for index, station in enumerate(self.stations):
            logger.info('Interpolating model run %s (%s/%s) for %s:%s',
                        model_run.id,
                        index, self.station_count,
                        station.code, station.name)
            # Process this model run for station.
            self._process_model_run_for_station(model_run, station)
        # Commit all the weather station model predictions (it's fast if we line them all up and commit
        # them in one go.)
        logger.info('commit to database...')
        self.session.commit()
        logger.info('done commit.')

    def _process_prediction(self,  # pylint: disable=too-many-arguments
                            prediction: ModelRunGridSubsetPrediction,
                            station: WeatherStation,
                            model_run: PredictionModelRunTimestamp,
                            points: List,
                            coordinate: List,
                            machine: StationMachineLearning):
        """ NOTE: Re. using griddata to interpolate:

        We're interpolating using degrees, as such we're introducing a slight
        innacuracy since degrees != distance. (i.e. This distance between two
        points at the bottom of a grid, isn't the same as the distance at the
        top.)

        It would be more accurate to interpolate towards the point of interest
        based on the distance of that point from the grid points.

        One could:
        a) convert all points from degrees to meters in UTM,
           and then interpolate - that should be slightly more accurate, e.g.:
        ```
        def transform(long, lat):
            # Transform NAD83 long and lat into UTM meters.
            zone = math.floor((long + 180) / 6) + 1
            utmProjection = "+proj=utm +zone={zone} +ellps=GRS80 +datum=NAD83 +units=m +no_defs".format(
                zone=zone)
            proj = Proj(utmProjection)
            return proj(long, lat)
        ```
        b) use something else fancy like inverse distance weighting.

        HOWEVER, the accuracy we gain is very little, it's adding an error of less than
        100 meters on the global model. (Which typically results in the 3rd decimal value
        of the interpolated value differing.)

        More accuracy can be gained by taking into account altitude differences between
        points and adjusting accordingly.
        """
        # If there's already a prediction, we want to update it
        station_prediction = get_weather_station_model_prediction(
            self.session, station.code, model_run.id, prediction.prediction_timestamp)
        if station_prediction is None:
            station_prediction = WeatherStationModelPrediction()
        # Populate the weather station prediction object.
        station_prediction.station_code = station.code
        station_prediction.prediction_model_run_timestamp_id = model_run.id
        station_prediction.prediction_timestamp = prediction.prediction_timestamp
        # Calculate the interpolated values.
        # 2020 Dec 15, Sybrand: Encountered situation where tmp_tgl_2 was None, add this workaround for it.
        # NOTE: Not sure why this value would ever be None. This could happen if for whatever reason, the
        # tmp_tgl_2 layer failed to download and process, while other layers did.
        if prediction.tmp_tgl_2 is None:
            logger.warning('tmp_tgl_2 is None for ModelRunGridSubsetPrediction.id == %s', prediction.id)
        else:
            station_prediction.tmp_tgl_2 = griddata(
                points, prediction.tmp_tgl_2, coordinate, method='linear')[0]

        # 2020 Dec 10, Sybrand: Encountered situation where rh_tgl_2 was None, add this workaround for it.
        # NOTE: Not sure why this value would ever be None. This could happen if for whatever reason, the
        # rh_tgl_2 layer failed to download and process, while other layers did.
        if prediction.rh_tgl_2 is None:
            # This is unexpected, so we log it.
            logger.warning('rh_tgl_2 is None for ModelRunGridSubsetPrediction.id == %s', prediction.id)
            station_prediction.rh_tgl_2 = None
        else:
            station_prediction.rh_tgl_2 = griddata(
                points, prediction.rh_tgl_2, coordinate, method='linear')[0]
        # Check that apcp_sfc_0 is None, since accumulated precipitation
        # does not exist for 00 hour.
        if prediction.apcp_sfc_0 is None:
            station_prediction.apcp_sfc_0 = 0.0
        else:
            station_prediction.apcp_sfc_0 = griddata(
                points, prediction.apcp_sfc_0, coordinate, method='linear')[0]
        # Calculate the delta_precipitation based on station's previous prediction_timestamp
        # for the same model run
        # For some reason pylint doesn't think session has a flush!
        self.session.flush()  # pylint: disable=no-member
        station_prediction.delta_precip = self._calculate_delta_precip(
            station, model_run, prediction, station_prediction)

        # Get the closest wind speed
        if prediction.wind_tgl_10 is not None:
            station_prediction.wind_tgl_10 = prediction.wind_tgl_10[get_closest_index(coordinate, points)]
        # Get the closest wind direcion
        if prediction.wdir_tgl_10 is not None:
            station_prediction.wdir_tgl_10 = prediction.wdir_tgl_10[get_closest_index(coordinate, points)]

        # Predict the temperature
        station_prediction.bias_adjusted_temperature = machine.predict_temperature(
            station_prediction.tmp_tgl_2,
            station_prediction.prediction_timestamp)
        # Predict the rh
        station_prediction.bias_adjusted_rh = machine.predict_rh(
            station_prediction.rh_tgl_2, station_prediction.prediction_timestamp)
        # Update the update time (this might be an update)
        station_prediction.update_date = time_utils.get_utc_now()
        # Add this prediction to the session (we'll commit it later.)
        self.session.add(station_prediction)

    def _calculate_delta_precip(self, station, model_run, prediction, station_prediction):
        """ Calculate the station_prediction's delta_precip based on the previous precip
        prediction for the station
        """
        results = self.session.query(WeatherStationModelPrediction).\
            filter(WeatherStationModelPrediction.station_code == station.code).\
            filter(WeatherStationModelPrediction.prediction_model_run_timestamp_id == model_run.id).\
            filter(WeatherStationModelPrediction.prediction_timestamp < prediction.prediction_timestamp).\
            order_by(WeatherStationModelPrediction.prediction_timestamp.desc()).\
            limit(1).first()
        # If there exists a previous prediction for the station from the same model run
        if results is not None:
            return station_prediction.apcp_sfc_0 - results.apcp_sfc_0
        # If there is no prior prediction within the same model run, it means that station_prediction is
        # the first prediction with apcp for the current model run (hour 001 or 003, depending on the
        # model type). In this case, delta_precip will be equal to the apcp
        return station_prediction.apcp_sfc_0

    def _process_model_run_for_station(self,
                                       model_run: PredictionModelRunTimestamp,
                                       station: WeatherStation):
        """ Process the model run for the provided station.
        """
        # Extract the coordinate.
        coordinate = [station.long, station.lat]
        # Lookup the grid our weather station is in.
        logger.info("Getting grid for coordinate %s and model %s",
                    coordinate, model_run.prediction_model)
        # There should never be more than one grid per model - but it can happen.
        # TODO: Re-factor away the need for the grid table entirely.
        grid_query = get_grids_for_coordinate(
            self.session, model_run.prediction_model, coordinate)

        for grid in grid_query:
            # Convert the grid database object to a polygon object.
            poly = to_shape(grid.geom)
            # Extract the vertices of the polygon.
            # pylint: disable=no-member
            points = list(poly.exterior.coords)[:-1]

            machine = StationMachineLearning(
                session=self.session,
                model=model_run.prediction_model,
                grid=grid,
                points=points,
                target_coordinate=coordinate,
                station_code=station.code,
                max_learn_date=model_run.prediction_run_timestamp)
            machine.learn()

            # Get all the predictions associated to this particular model run, in the grid.
            query = get_model_run_predictions_for_grid(
                self.session, model_run, grid)

            # Iterate through all the predictions.
            prev_prediction = None
            for prediction in query:
                if (prev_prediction is not None
                        and prev_prediction.prediction_timestamp.hour == 18
                        and prediction.prediction_timestamp.hour == 21):
                    noon_prediction = construct_interpolated_noon_prediction(prev_prediction, prediction)
                    self._process_prediction(
                        noon_prediction, station, model_run, points, coordinate, machine)
                self._process_prediction(
                    prediction, station, model_run, points, coordinate, machine)
                prev_prediction = prediction

    def _mark_model_run_interpolated(self, model_run: PredictionModelRunTimestamp):
        """ Having completely processed a model run, we can mark it has having been interpolated.
        """
        model_run.interpolated = True
        logger.info('marking %s as interpolated', model_run)
        self.session.add(model_run)
        self.session.commit()

    def process(self, model_type: ModelEnum):
        """ Entry point to start processing model runs that have not yet had their predictions interpolated
        """
        # Get model runs that are complete (fully downloaded), but not yet interpolated.
        query = get_prediction_model_run_timestamp_records(
            self.session, complete=True, interpolated=False, model_type=model_type)
        for model_run, model in query:
            logger.info('model %s', model)
            logger.info('model_run %s', model_run)
            # Process the model run.
            self._process_model_run(model_run)
            # Mark the model run as interpolated.
            self._mark_model_run_interpolated(model_run)
