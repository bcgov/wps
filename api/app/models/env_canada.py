""" A script that downloads weather models from Environment Canada HTTP data server
TODO: Move this file to app/models/ (not part of this PR as it makes comparing prev. version difficult -
      there are so many changes, it's picked up as a delete instead of a move.)
"""

import os
import sys
import datetime
from typing import Generator, List
from urllib.parse import urlparse
import logging
import time
import tempfile
import requests
from scipy.interpolate import griddata
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from app.db.crud import (get_processed_file_record,
                         get_processed_file_count,
                         get_prediction_model_run_timestamp_records,
                         get_model_run_predictions_for_grid,
                         get_grid_for_coordinate,
                         get_weather_station_model_prediction)
from app.models.machine_learning import StationMachineLearning
from app.models import ModelEnum, ProjectionEnum, construct_interpolated_noon_prediction
from app.schemas import WeatherStation
from app import configure_logging
import app.time_utils as time_utils
from app.stations import get_stations_synchronously
from app.models.process_grib import GribFileProcessor, ModelRunInfo
from app.db.models import (ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           WeatherStationModelPrediction, ModelRunGridSubsetPrediction)
import app.db.database

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


class UnhandledPredictionModelType(Exception):
    """ Exception raised when an unknown model type is encountered. """


def parse_global_model_filename(filename):
    """ Parse filename for GDPS grib file to extract metadata """
    base = os.path.basename(filename)
    parts = base.split('_')
    model = parts[1]
    variable = parts[2]
    level_type = parts[3]
    level = parts[4]
    variable_name = '_'.join(
        [variable, level_type, level])
    projection = parts[5]
    prediction_start = parts[6][:-2]
    run_time = parts[6][-2:]
    model_run_timestamp = datetime.datetime(
        year=int(prediction_start[:4]),
        month=int(prediction_start[4:6]),
        day=int(prediction_start[6:8]),
        hour=int(run_time), tzinfo=datetime.timezone.utc)
    last_part = parts[7].split('.')
    prediction_hour = last_part[0][1:]
    prediction_timestamp = model_run_timestamp + \
        datetime.timedelta(hours=int(prediction_hour))
    return model, variable_name, projection, model_run_timestamp, prediction_timestamp


def parse_high_res_model_filename(filename):
    """ Parse filename for HRDPS grib file to extract metadata """
    base = os.path.basename(filename)
    parts = base.split('_')
    model = '_'.join([parts[1], parts[2]])
    variable = parts[3]
    level_type = parts[4]
    level = parts[5]
    variable_name = '_'.join(
        [variable, level_type, level])
    projection = parts[6]
    prediction_start = parts[7][:-2]
    run_time = parts[7][-2:]
    model_run_timestamp = datetime.datetime(
        year=int(prediction_start[:4]),
        month=int(prediction_start[4:6]),
        day=int(prediction_start[6:8]),
        hour=int(run_time), tzinfo=datetime.timezone.utc)
    last_part = parts[8].split('.')
    prediction_hour = last_part[0][1:4]
    prediction_timestamp = model_run_timestamp + \
        datetime.timedelta(hours=int(prediction_hour))
    return model, variable_name, projection, model_run_timestamp, prediction_timestamp


def parse_env_canada_filename(filename):
    """ Take a grib filename, as per file name nomenclature defined at
    https://weather.gc.ca/grib/grib2_glb_25km_e.html, and parse into a meaningful object.
    """
    # pylint: disable=too-many-locals
    base = os.path.basename(filename)
    parts = base.split('_')
    model = parts[1]
    if model == 'glb':
        model, variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_global_model_filename(filename)
        model_abbreviation = ModelEnum.GDPS
    elif model == 'hrdps':
        model, variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_high_res_model_filename(filename)
        model_abbreviation = ModelEnum.HRDPS
    elif model == 'reg':
        model_abbreviation = ModelEnum.RDPS
        # NOTE: function to parse RDPS filenames has not been written yet
    else:
        raise UnhandledPredictionModelType(
            'Unhandled prediction model type found', model)

    info = ModelRunInfo()
    info.model_abbreviation = model_abbreviation
    info.projection = projection
    info.model_run_timestamp = model_run_timestamp
    info.prediction_timestamp = prediction_timestamp
    info.variable_name = variable_name
    return info


def adjust_model_day(now, model_run_hour) -> datetime:
    """ Adjust the model day, based on the current time.

    If now (e.g. 10h00) is less than model run (e.g. 12), it means we have to look for yesterdays
    model run.
    """
    if now.hour < model_run_hour:
        return now - datetime.timedelta(days=1)
    return now


def get_file_date_part(now, model_run_hour) -> str:
    """ Construct the part of the filename that contains the model run date
    """
    adjusted = adjust_model_day(now, model_run_hour)
    date = '{year}{month:02d}{day:02d}'.format(
        year=adjusted.year, month=adjusted.month, day=adjusted.day)
    return date


def get_model_run_hours(model_abbreviation: str):
    """ Yield model run hours for GDPS (00h00 and 12h00) """
    if model_abbreviation == ModelEnum.GDPS:
        for hour in [0, 12]:
            yield hour
    elif model_abbreviation == ModelEnum.HRDPS:
        for hour in [0, 6, 12, 18]:
            yield hour


def get_global_model_run_download_urls(now: datetime.datetime,
                                       model_run_hour: int) -> Generator[str, None, None]:
    """ Yield urls to download GDPS (global) model runs """

    # hh: model run start, in UTC [00, 12]
    # hhh: prediction hour [000, 003, 006, ..., 240]
    # pylint: disable=invalid-name
    hh = '{:02d}'.format(model_run_hour)
    # For the global model, we have prediction at 3 hour intervals up to 240 hours.
    for h in range(0, 241, 3):
        hhh = format(h, '03d')
        for level in ['TMP_TGL_2', 'RH_TGL_2']:
            base_url = 'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{}/{}/'.format(
                hh, hhh)
            date = get_file_date_part(now, model_run_hour)
            filename = 'CMC_glb_{}_latlon.15x.15_{}{}_P{}.grib2'.format(
                level, date, hh, hhh)
            url = base_url + filename
            yield url


def get_high_res_model_run_download_urls(now: datetime.datetime, hour: int) -> Generator[str, None, None]:
    """ Yield urls to download HRDPS (high-res) model runs """
    # pylint: disable=invalid-name
    hh = '{:02d}'.format(hour)
    # For the high-res model, predictions are at 1 hour intervals up to 48 hours.
    for h in range(0, 49):
        hhh = format(h, '03d')
        for level in ['TMP_TGL_2', 'RH_TGL_2']:
            base_url = 'https://dd.weather.gc.ca/model_hrdps/continental/grib2/{}/{}/'.format(
                hh, hhh)
            date = get_file_date_part(now, hour)
            filename = 'CMC_hrdps_continental_{}_ps2.5km_{}{}_P{}-00.grib2'.format(
                level, date, hh, hhh)
            url = base_url + filename
            yield url


def download(url: str, path: str) -> str:
    """
    Download a file from a url.
    NOTE: was using wget library initially, but has the drawback of not being able to control where the
    temporary files are stored. This is problematic, as giving the application write access to /app
    is a security concern.
    """
    # Infer filename from url.
    filename = os.path.split(url)[-1]
    # Construct target location for downloaded file.
    target = os.path.join(os.getcwd(), path, filename)
    # Get the file.
    # It's important to have a timeout on the get, otherwise the call may get stuck for an indefinite
    # amount of time - there is no default value for timeout. During testing, it was observed that
    # downloads usually complete in less than a second.
    logger.info('downloading %s', url)
    response = requests.get(url, timeout=60)
    # If the response is 200/OK.
    if response.status_code == 200:
        # Store the response.
        with open(target, 'wb') as file_object:
            # Write the file.
            file_object.write(response.content)
    elif response.status_code == 404:
        # We expect this to happen frequently - just log for info.
        logger.info('404 error for %s', url)
        target = None
    else:
        # Raise an exception
        response.raise_for_status()
    # Return file location.
    return target


def mark_prediction_model_run_processed(session: Session,
                                        model: ModelEnum,
                                        projection: ProjectionEnum,
                                        now: datetime.datetime,
                                        model_run_hour: int):
    """ Mark a prediction model run as processed (complete) """

    prediction_model = app.db.crud.get_prediction_model(
        session, model, projection)
    prediction_run_timestamp = datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour, tzinfo=datetime.timezone.utc)
    prediction_run_timestamp = adjust_model_day(
        prediction_run_timestamp, model_run_hour)
    prediction_run_timestamp = prediction_run_timestamp.replace(
        hour=model_run_hour)
    logger.info('prediction_model:%s, prediction_run_timestamp:%s',
                prediction_model, prediction_run_timestamp)
    prediction_run = app.db.crud.get_prediction_run(
        session,
        prediction_model.id,
        prediction_run_timestamp)
    logger.info('prediction run: %s', prediction_run)
    prediction_run.complete = True
    app.db.crud.update_prediction_run(session, prediction_run)


class EnvCanada():
    """ Class that orchestrates downloading and processing of weather model grib files from environment
    Canada.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, model_type):
        """ Prep variables """
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.session = app.db.database.get_write_session()
        self.grib_processor = GribFileProcessor()
        self.model_type = ModelEnum(model_type)
        # set projection based on model_type
        if self.model_type == ModelEnum.GDPS:
            self.projection = ProjectionEnum.LATLON_15X_15
        elif self.model_type == ModelEnum.HRDPS:
            self.projection = ProjectionEnum.HIGH_RES_CONTINENTAL

    def flag_file_as_processed(self, url):
        """ Flag the file as processed in the database """
        processed_file = get_processed_file_record(self.session, url)
        if processed_file:
            logger.info('re-procesed %s', url)
        else:
            logger.info('file processed %s', url)
            processed_file = ProcessedModelRunUrl(
                url=url,
                create_date=time_utils.get_utc_now())
        processed_file.update_date = time_utils.get_utc_now()
        # pylint: disable=no-member
        self.session.add(processed_file)
        self.session.commit()

    def check_if_model_run_complete(self, urls):
        """ Check if a particular model run is complete """
        # pylint: disable=no-member
        actual_count = get_processed_file_count(self.session, urls)
        expected_count = len(urls)
        logger.info('we have processed %s/%s files',
                    actual_count, expected_count)
        return actual_count == expected_count

    def process_model_run_urls(self, urls):
        """ Process the urls for a model run.
        """
        for url in urls:
            try:
                # check the database for a record of this file:
                processed_file_record = get_processed_file_record(
                    self.session, url)
                if processed_file_record:
                    # This file has already been processed - so we skip it.
                    logger.info('file already processed %s', url)
                else:
                    # extract model info from filename:
                    filename = os.path.basename(urlparse(url).path)
                    model_info = parse_env_canada_filename(filename)
                    # download the file:
                    with tempfile.TemporaryDirectory() as tmp_path:
                        downloaded = download(url, tmp_path)
                        if downloaded:
                            self.files_downloaded += 1
                            # If we've downloaded the file ok, we can now process it.
                            try:
                                self.grib_processor.process_grib_file(
                                    downloaded, model_info)
                                # Flag the file as processed
                                self.flag_file_as_processed(url)
                                self.files_processed += 1
                            finally:
                                # delete the file when done.
                                os.remove(downloaded)
            # pylint: disable=broad-except
            except Exception as exception:
                self.exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.error('unexpected exception processing %s',
                             url, exc_info=exception)

    def process_model_run(self, model_run_hour):
        """ Process a particular model run """
        logger.info('Processing {} model run {:02d}'.format(
            self.model_type, model_run_hour))

        # Get the urls for the current model run.
        if self.model_type == ModelEnum.GDPS:
            urls = list(get_global_model_run_download_urls(
                self.now, model_run_hour))
        elif self.model_type == ModelEnum.HRDPS:
            urls = list(get_high_res_model_run_download_urls(
                self.now, model_run_hour))

        # Process all the urls.
        self.process_model_run_urls(urls)

        # Having completed processing, check if we're all done.
        if self.check_if_model_run_complete(urls):
            logger.info(
                '{} model run {:02d}:00 completed with SUCCESS'.format(self.model_type, model_run_hour))

            mark_prediction_model_run_processed(
                self.session, self.model_type, self.projection, self.now, model_run_hour)

    def process(self):
        """ Entry point for downloading and processing weather model grib files """
        for hour in get_model_run_hours(self.model_type):
            try:
                self.process_model_run(hour)
            # pylint: disable=broad-except
            except Exception as exception:
                # We catch and log exceptions, but keep trying to process.
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error(
                    'unexpected exception processing %s model run %d',
                    self.model_type, hour, exc_info=exception)


class ModelValueProcessor:
    """ Iterate through model runs that have completed, and calculate the interpolated weather predictions.
    """

    def __init__(self):
        """ Prepare variables we're going to use throughout """
        self.session = app.db.database.get_write_session()
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
        station_prediction.tmp_tgl_2 = griddata(
            points, prediction.tmp_tgl_2, coordinate, method='linear')[0]
        station_prediction.rh_tgl_2 = griddata(
            points, prediction.rh_tgl_2, coordinate, method='linear')[0]
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

    def _process_model_run_for_station(self,
                                       model_run: PredictionModelRunTimestamp,
                                       station: WeatherStation):
        """ Process the model run for the prodvided station.
        """
        # Extract the coordinate.
        coordinate = [station.long, station.lat]
        # Lookup the grid our weather station is in.
        logger.info("Getting grid for coordinate %s and model %s",
                    coordinate, model_run.prediction_model)
        grid = get_grid_for_coordinate(
            self.session, model_run.prediction_model, coordinate)

        # Convert the grid database object to a polygon object.
        poly = to_shape(grid.geom)
        # Extract the vertices of the polygon.
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
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction)
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

    def process(self, model_type: str):
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


def main():
    """ main script """

    # set the model type requested based on arg passed via command line
    model_type = sys.argv[1]
    logger.info('model type %s', model_type)

    # grab the start time.
    start_time = time.time()

    # process everything.
    env_canada = EnvCanada(model_type)
    env_canada.process()

    # interpolate and machine learn everything that needs interpolating.
    model_value_processor = ModelValueProcessor()
    model_value_processor.process(model_type)

    # calculate the execution time.
    execution_time = round(time.time() - start_time, 1)
    # log some info.
    logger.info('%d downloaded, %d processed in total, took %s seconds',
                env_canada.files_downloaded, env_canada.files_processed, execution_time)
    # check if we encountered any exceptions.
    if env_canada.exception_count > 0:
        # if there were any exceptions, return a non-zero status.
        logger.warning('completed processing with some exceptions')
        sys.exit(os.EX_SOFTWARE)
    return env_canada.files_processed


if __name__ == "__main__":
    try:
        main()
    # pylint: disable=broad-except
    except Exception as exception:
        # We catch and log any exceptions we may have missed.
        logger.error('unexpected exception processing', exc_info=exception)
        # Exit with a failure code.
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)
