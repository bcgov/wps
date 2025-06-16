""" A script that downloads weather models from Environment Canada HTTP data server
https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/issues/bcgov/wps/1601
"""
import os
import sys
import datetime
from urllib.parse import urlparse
import logging
import tempfile
from sqlalchemy.orm import Session
from wps_shared.db.database import get_read_session_scope, get_write_session_scope
from wps_shared.db.crud.weather_models import (
    get_processed_file_record,
    get_prediction_model,
    get_prediction_run,
    update_prediction_run,
)
from wps_shared.weather_models.job_utils import (
    get_model_run_urls,
)
from wps_jobs.weather_model_jobs.common_model_fetchers import (
    ModelValueProcessor,
    apply_data_retention_policy,
    check_if_model_run_complete,
    flag_file_as_processed,
)
from wps_shared.weather_models import ModelEnum, ProjectionEnum, get_env_canada_model_run_hours, UnhandledPredictionModelType
from wps_shared.wps_logging import configure_logging
import wps_shared.utils.time as time_utils
from wps_jobs.weather_model_jobs.utils.process_grib import (
    GribFileProcessor,
    ModelRunInfo,
)
import wps_shared.db.database
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.weather_models import (
    adjust_model_day,
    CompletedWithSomeExceptions,
    download,
)

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)

def parse_gdps_rdps_filename(filename):
    """ Parse filename for GDPS grib file to extract metadata """
    base = os.path.basename(filename)
    parts = base.split('_')
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
    return variable_name, projection, model_run_timestamp, prediction_timestamp


def parse_high_res_model_url(url):
    """ Parse filename for HRDPS grib file to extract metadata """
    base = os.path.basename(url)
    base_parts = base.split('_')
    url_parts = url.split('/')
    try:
        variable = base_parts[3]
        level = base_parts[4]
        variable_name = '_'.join(
            [variable, level])
        projection = ProjectionEnum.HIGH_RES_CONTINENTAL
        run_date_str = base_parts[0][:-4]
        run_hour_str = url_parts[6]
        model_run_timestamp = datetime.datetime(
            year=int(run_date_str[:4]),
            month=int(run_date_str[4:6]),
            day=int(run_date_str[6:8]),
            hour=int(run_hour_str),
            tzinfo=datetime.timezone.utc
        )
        prediction_hour = url_parts[7]
        prediction_timestamp = model_run_timestamp + \
            datetime.timedelta(hours=int(prediction_hour))
        return variable_name, projection, model_run_timestamp, prediction_timestamp
    except Exception as exc:
        logger.error('HRDPS URL %s is not in the expected format', url)
        logger.error(exc_info=exc)


def parse_env_canada_filename(url):
    """ Take a grib url, as per file name nomenclature defined at
    https://weather.gc.ca/grib/grib2_glb_25km_e.html, and parse into a meaningful object.
    """
    filename = os.path.basename(urlparse(url).path)
    base = os.path.basename(filename)
    parts = base.split('_')
    if 'glb' in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_gdps_rdps_filename(filename)
        model_enum = ModelEnum.GDPS
    elif 'HRDPS' in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_high_res_model_url(url)
        model_enum = ModelEnum.HRDPS
    elif 'reg' in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = \
            parse_gdps_rdps_filename(filename)
        model_enum = ModelEnum.RDPS
    else:
        raise UnhandledPredictionModelType(
            'Unhandled prediction model type found', filename)

    info = ModelRunInfo()
    info.model_enum = model_enum
    info.projection = projection
    info.model_run_timestamp = model_run_timestamp
    info.prediction_timestamp = prediction_timestamp
    info.variable_name = variable_name
    return info


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

    def __init__(self, session: Session, model_type: ModelEnum):
        """ Prep variables """
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.grib_processor = GribFileProcessor()
        self.model_type: ModelEnum = model_type
        self.session = session
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
                # check the database for a record of this file:
                processed_file_record = get_processed_file_record(self.session, url)
                if processed_file_record:
                    # This file has already been processed - so we skip it.
                    # NOTE: changing this to logger.debug causes too much noise in unit tests.
                    logger.debug("file already processed %s", url)
                else:
                    # extract model info from URL:
                    model_info = parse_env_canada_filename(url)
                    # download the file:
                    with tempfile.TemporaryDirectory() as temporary_path:
                        downloaded = download(url, temporary_path, "REDIS_CACHE_ENV_CANADA", model_info.model_enum.value, "REDIS_ENV_CANADA_CACHE_EXPIRY")
                        if downloaded:
                            self.files_downloaded += 1
                            # If we've downloaded the file ok, we can now process it.
                            try:
                                self.grib_processor.process_grib_file(downloaded, model_info, self.session)
                                # Flag the file as processed
                                flag_file_as_processed(url, self.session)
                                self.files_processed += 1
                            finally:
                                # delete the file when done.
                                os.remove(downloaded)
            except Exception as exception:
                self.exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.error("unexpected exception processing %s", url, exc_info=exception)

    def process_model_run(self, model_run_hour):
        """ Process a particular model run """
        logger.info('Processing {} model run {:02d}'.format(
            self.model_type, model_run_hour))

        # Get the urls for the current model run.
        urls = get_model_run_urls(self.now, self.model_type, model_run_hour)

        # Process all the urls.
        self.process_model_run_urls(urls)

        # Having completed processing, check if we're all done.
        if check_if_model_run_complete(self.session, urls):
            logger.info("{} model run {:02d}:00 completed with SUCCESS".format(self.model_type, model_run_hour))

            mark_prediction_model_run_processed(self.session, self.model_type, self.projection, self.now, model_run_hour)

    def process(self):
        """ Entry point for downloading and processing weather model grib files """
        for hour in get_env_canada_model_run_hours(self.model_type):
            try:
                self.process_model_run(hour)
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

    with (
        get_write_session_scope() as write_session,
        get_read_session_scope() as read_session,
    ):
        env_canada = EnvCanada(write_session, model_type)
        env_canada.process()

        # interpolate and machine learn everything that needs interpolating.
        model_value_processor = ModelValueProcessor(write_session, read_session)
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
    except Exception as exception:
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
