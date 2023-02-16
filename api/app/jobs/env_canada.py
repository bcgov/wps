""" A script that downloads weather models from Environment Canada HTTP data server
https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/issues/bcgov/wps/1601
"""
import os
import sys
import datetime
from typing import Generator, List
from urllib.parse import urlparse
import logging
import tempfile
from scipy.interpolate import griddata
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from app.db.crud.weather_models import (get_processed_file_record,
                                        get_prediction_model_run_timestamp_records,
                                        get_model_run_predictions_for_grid,
                                        get_grids_for_coordinate,
                                        get_weather_station_model_prediction,
                                        delete_model_run_grid_subset_predictions,
                                        get_prediction_model,
                                        get_prediction_run,
                                        update_prediction_run)
from app.jobs.common_model_fetchers import (CompletedWithSomeExceptions, ModelValueProcessor, UnhandledPredictionModelType, apply_data_retention_policy,
                                            check_if_model_run_complete, download, flag_file_as_processed, get_closest_index)
from app.weather_models.machine_learning import StationMachineLearning
from app.weather_models import ModelEnum, ProjectionEnum, construct_interpolated_noon_prediction
from app.schemas.stations import WeatherStation
from app import configure_logging
import app.utils.time as time_utils
from app.stations import get_stations_synchronously
from app.weather_models.process_grib import GribFileProcessor, ModelRunInfo
from app.db.models import (PredictionModelRunTimestamp,
                           WeatherStationModelPrediction, ModelRunGridSubsetPrediction)
import app.db.database
from app.rocketchat_notifications import send_rocketchat_notification

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


GRIB_LAYERS = ('TMP_TGL_2', 'RH_TGL_2', 'APCP_SFC_0', 'WDIR_TGL_10', 'WIND_TGL_10')


def parse_gdps_rdps_filename(filename):
    """ Parse filename for GDPS grib file to extract metadata """
    base = os.path.basename(filename)
    parts = base.split('_')
    model = parts[1]
    variable = parts[2]
    level_type = parts[3]
    level = parts[4]
    variable_name = '_'.join(
        [variable, level_type, level])
    projection = ProjectionEnum(parts[5])
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
    projection = ProjectionEnum(parts[6])
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
            parse_gdps_rdps_filename(filename)
        model_enum = ModelEnum.GDPS
    elif model == 'hrdps':
        model, variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_high_res_model_filename(filename)
        model_enum = ModelEnum.HRDPS
    elif model == 'reg':
        model, variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_gdps_rdps_filename(filename)
        model_enum = ModelEnum.RDPS
    else:
        raise UnhandledPredictionModelType(
            'Unhandled prediction model type found', model)

    info = ModelRunInfo()
    info.model_enum = model_enum
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
    date = f"{adjusted.year}{adjusted.month:02d}{adjusted.day:02d}"
    return date


def get_model_run_hours(model_type: ModelEnum):
    """ Yield model run hours for GDPS (00h00 and 12h00) """
    if model_type == ModelEnum.GDPS:
        for hour in [0, 12]:
            yield hour
    elif model_type in (ModelEnum.HRDPS, ModelEnum.RDPS):
        for hour in [0, 6, 12, 18]:
            yield hour


def get_model_run_urls(now: datetime.datetime, model_type: ModelEnum, model_run_hour: int):
    """ Get model run url's """
    if model_type == ModelEnum.GDPS:
        return list(get_global_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.HRDPS:
        return list(get_high_res_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.RDPS:
        return list(get_regional_model_run_download_urls(now, model_run_hour))
    raise UnhandledPredictionModelType()


def get_global_model_run_download_urls(now: datetime.datetime,
                                       model_run_hour: int) -> Generator[str, None, None]:
    """ Yield urls to download GDPS (global) model runs """

    # hh: model run start, in UTC [00, 12]
    # hhh: prediction hour [000, 003, 006, ..., 240]
    # pylint: disable=invalid-name
    hh = f"{model_run_hour:02d}"
    # For the global model, we have prediction at 3 hour intervals up to 240 hours.
    for h in range(0, 241, 3):
        hhh = format(h, '03d')
        for level in GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if (hhh == '000' and level == 'APCP_SFC_0'):
                continue
            base_url = f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{hh}/{hhh}/'
            date = get_file_date_part(now, model_run_hour)
            filename = f'CMC_glb_{level}_latlon.15x.15_{date}{hh}_P{hhh}.grib2'
            url = base_url + filename
            yield url


def get_high_res_model_run_download_urls(now: datetime.datetime, hour: int) -> Generator[str, None, None]:
    """ Yield urls to download HRDPS (high-res) model runs """
    # pylint: disable=invalid-name
    hh = f"{hour:02d}"
    # For the high-res model, predictions are at 1 hour intervals up to 48 hours.
    for h in range(0, 49):
        hhh = format(h, '03d')
        for level in GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if (hhh == '000' and level == 'APCP_SFC_0'):
                continue
            base_url = f'https://dd.weather.gc.ca/model_hrdps/continental/grib2/{hh}/{hhh}/'
            date = get_file_date_part(now, hour)
            filename = f'CMC_hrdps_continental_{level}_ps2.5km_{date}{hh}_P{hhh}-00.grib2'
            url = base_url + filename
            yield url


def get_regional_model_run_download_urls(now: datetime.datetime, hour: int) -> Generator[str, None, None]:
    """ Yield urls to download RDPS model runs """
    # pylint: disable=invalid-name
    hh = f"{hour:02d}"
    # For the RDPS model, predictions are at 1 hour intervals up to 84 hours.
    for h in range(0, 85):
        hhh = format(h, '03d')
        for level in GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if (hhh == '000' and level == 'APCP_SFC_0'):
                continue
            base_url = f'https://dd.weather.gc.ca/model_gem_regional/10km/grib2/{hh}/{hhh}/'
            date = get_file_date_part(now, hour)
            filename = f'CMC_reg_{level}_ps10km_{date}{hh}_P{hhh}.grib2'
            url = base_url + filename
            yield url


def mark_prediction_model_run_processed(session: Session,
                                        model: ModelEnum,
                                        projection: ProjectionEnum,
                                        now: datetime.datetime,
                                        model_run_hour: int):
    """ Mark a prediction model run as processed (complete) """

    prediction_model = get_prediction_model(session, model, projection)
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
    prediction_run = get_prediction_run(session,
                                        prediction_model.id,
                                        prediction_run_timestamp)
    logger.info('prediction run: %s', prediction_run)
    prediction_run.complete = True
    update_prediction_run(session, prediction_run)


class EnvCanada():
    """ Class that orchestrates downloading and processing of weather model grib files from environment
    Canada.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, model_type: ModelEnum):
        """ Prep variables """
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.grib_processor = GribFileProcessor()
        self.model_type: ModelEnum = model_type
        # set projection based on model_type
        if self.model_type == ModelEnum.GDPS:
            self.projection = ProjectionEnum.LATLON_15X_15
        elif self.model_type == ModelEnum.HRDPS:
            self.projection = ProjectionEnum.HIGH_RES_CONTINENTAL
        elif self.model_type == ModelEnum.RDPS:
            self.projection = ProjectionEnum.REGIONAL_PS
        else:
            raise UnhandledPredictionModelType(f'Unknown model type: {self.model_type}')

    def process_model_run_urls(self, urls):
        """ Process the urls for a model run.
        """
        for url in urls:
            try:
                with app.db.database.get_write_session_scope() as session:
                    # check the database for a record of this file:
                    processed_file_record = get_processed_file_record(session, url)
                    if processed_file_record:
                        # This file has already been processed - so we skip it.
                        # NOTE: changing this to logger.debug causes too much noise in unit tests.
                        logger.debug('file already processed %s', url)
                    else:
                        # extract model info from filename:
                        filename = os.path.basename(urlparse(url).path)
                        model_info = parse_env_canada_filename(filename)
                        # download the file:
                        with tempfile.TemporaryDirectory() as temporary_path:
                            downloaded = download(url, temporary_path, 'REDIS_CACHE_ENV_CANADA',
                                                  'REDIS_ENV_CANADA_CACHE_EXPIRY')
                            if downloaded:
                                self.files_downloaded += 1
                                # If we've downloaded the file ok, we can now process it.
                                try:
                                    self.grib_processor.process_grib_file(
                                        downloaded, model_info, session)
                                    # Flag the file as processed
                                    flag_file_as_processed(url, session)
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
        # pylint: disable=consider-using-f-string
        logger.info('Processing {} model run {:02d}'.format(
            self.model_type, model_run_hour))

        # Get the urls for the current model run.
        urls = get_model_run_urls(self.now, self.model_type, model_run_hour)

        # Process all the urls.
        self.process_model_run_urls(urls)

        # Having completed processing, check if we're all done.
        with app.db.database.get_write_session_scope() as session:
            if check_if_model_run_complete(session, urls):
                # pylint: disable=consider-using-f-string
                logger.info(
                    '{} model run {:02d}:00 completed with SUCCESS'.format(self.model_type, model_run_hour))

                mark_prediction_model_run_processed(
                    session, self.model_type, self.projection, self.now, model_run_hour)

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


def process_models():
    """ downloading and processing models """

    # set the model type requested based on arg passed via command line
    model_type = ModelEnum(sys.argv[1])
    logger.info('model type %s', model_type)

    # grab the start time.
    start_time = datetime.datetime.now()

    env_canada = EnvCanada(model_type)
    env_canada.process()

    with app.db.database.get_write_session_scope() as session:
        # interpolate and machine learn everything that needs interpolating.
        model_value_processor = ModelValueProcessor(session)
        model_value_processor.process(model_type)

    # calculate the execution time.
    execution_time = datetime.datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # log some info.
    logger.info('%d downloaded, %d processed in total, time taken %d hours, %d minutes, %d seconds (%s)',
                env_canada.files_downloaded, env_canada.files_processed, hours, minutes, seconds,
                execution_time)
    # check if we encountered any exceptions.
    if env_canada.exception_count > 0:
        # if there were any exceptions, return a non-zero status.
        raise CompletedWithSomeExceptions()
    return env_canada.files_processed


def main():
    """ main script - process and download models, then do exception handling """
    try:
        process_models()
        apply_data_retention_policy()
    except CompletedWithSomeExceptions:
        logger.warning('completed processing with some exceptions')
        sys.exit(os.EX_SOFTWARE)
    except Exception as exception:  # pylint: disable=broad-except
        # We catch and log any exceptions we may have missed.
        logger.error('unexpected exception processing', exc_info=exception)
        rc_message = f':poop: Encountered error retrieving {sys.argv[1]} model data from Env Canada'
        send_rocketchat_notification(rc_message, exception)
        # Exit with a failure code.
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
