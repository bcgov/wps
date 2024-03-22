""" A script that downloads weather models from NCEI NOAA HTTPS data server
"""
import os
import sys
import datetime
from typing import Generator
import logging
import tempfile
from sqlalchemy.orm import Session
from ecmwf.opendata import Client
from app.db.crud.weather_models import (get_processed_file_record,
                                        get_prediction_model,
                                        get_prediction_run,
                                        update_prediction_run)
from app.jobs.common_model_fetchers import (CompletedWithSomeExceptions,
                                            apply_data_retention_policy, check_if_model_run_complete,
                                            download, flag_file_as_processed)
from app import configure_logging
import app.utils.time as time_utils
from app.weather_models import ModelEnum, ProjectionEnum
from app.weather_models.process_grib import GribFileProcessor, ModelRunInfo
import app.db.database
from app.stations import StationSourceEnum
from app.rocketchat_notifications import send_rocketchat_notification

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)

# ---- ECMWF static variables -------------#
ECMWF_BASE_URL = "https://data.ecmwf.int/forecasts"
ECMWF_IFS_MODEL = 'ifs'
ECMWF_HIGH_RES_FORECAST = 'oper'
ECMWF_GRID = '0p25'  # 0.25 degree grid
WX_VARS = ['r', 't', 'tp', '10u', '10v']
LEVELS = [1000]

# -------------------------------------- #


# ------- Static variables to be used for all NOAA models --------- #
# weather variables are APCP: total precip, TMP: temperature, UGRD: U-component of wind,
# VGRD: V-component of wind
# WX_VARS = ['APCP', 'RH', 'TMP', 'UGRD', 'VGRD']
# LEVELS = ['surface', '2_m_above_ground', '10_m_above_ground']
# SUBREGION_TOP_LAT = 60
# SUBREGION_BOTTOM_LAT = 48
# SUBREGION_LEFT_LON = -139
# SUBREGION_RIGHT_LON = -114
# -------------------------------------- #


def get_ecmwf_model_run_hours():
    """ Yield GFS and/or NAM model run hours (they're both on the same schedule)
     ("00", "06", "12", "18") """
    for hour in range(0, 19, 6):
        hour_str = format(hour, '02d')
        yield hour_str


def get_year_mo_date_string_from_datetime(datetime: datetime.datetime) -> str:
    """ Returns string for year_mo_date to be used when requesting
    grib files from NOAA"""
    year_mo_date = f"{datetime.year}" + format(datetime.month, '02d') + format(datetime.day, '02d')
    return year_mo_date


def get_ecmwf_wx_variables_filter_str() -> str:
    wx_vars_filter_str = ''
    for var in WX_VARS:
        wx_vars_filter_str += f'var_{var}=on&'

    return wx_vars_filter_str


def get_ecmwf_model_run_download_urls(download_date: datetime.datetime, model_cycle: str, client: Client) -> Generator[str, None, None]:
    """ Yield URLs to download ECMWF model runs.  """

    #  a step is a forecast time step expressed in hours from a base date (UTC) and base hour (00, 06, 12, 18)
    if model_cycle == '00' or model_cycle == '12':
        # The steps available are 0h to 144h by 3h and 150h to 240h by 6h
        steps = [step for step in range(0, 145, 3)] + [step for step in range(150, 241, 6)]
    elif model_cycle == '06' or model_cycle == '18':
        steps = [step for step in range(0, 91, 3)]

    dt = datetime.datetime(year=download_date.year, month=download_date.month, day=download_date.day, hour=int(model_cycle))
    HOURLY_PATTERN = (
    "{_url}/{_yyyymmdd}/{_H}z/{model}/{resol}/{_stream}/"
    "{_yyyymmddHHMMSS}-{step}h-{_stream}-{type}.{_extension}")
    for forecast_step in steps:
        url = f"""{ECMWF_BASE_URL}/{dt.strftime('%Y%m%d')}/{model_cycle}z/{ECMWF_IFS_MODEL}/{ECMWF_GRID}/{ECMWF_HIGH_RES_FORECAST}/{dt.strftime('%Y%m%d%H%M%S')}-{forecast_step}h-{ECMWF_HIGH_RES_FORECAST}-fc.grib2"""
        yield url



def parse_url_for_timestamps(url: str, model_type: ModelEnum):
    return []
    # if model_type == ModelEnum.GFS:
    #     return parse_gfs_url_for_timestamps(url)
    # elif model_type == ModelEnum.NAM:
    #     return parse_nam_url_for_timestamps(url)


def adjust_model_day(now, model_run_hour) -> datetime:
    """ Adjust the model day, based on the current time.

    If now (e.g. 10h00) is less than model run (e.g. 12), it means we have to look for yesterdays
    model run.
    """
    if now.hour < int(model_run_hour):
        return now - datetime.timedelta(days=1)
    return now


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
        hour=int(model_run_hour))
    logger.info('prediction_model:%s, prediction_run_timestamp:%s',
                prediction_model, prediction_run_timestamp)
    prediction_run = get_prediction_run(session,
                                        prediction_model.id,
                                        prediction_run_timestamp)
    logger.info('prediction run: %s', prediction_run)
    prediction_run.complete = True
    update_prediction_run(session, prediction_run)


class ECMWF():
    """ Class that orchestrates downloading and processing of GFS weather model grib files from NOAA.
    """

    def __init__(self, model_type: ModelEnum, station_source: StationSourceEnum = StationSourceEnum.UNSPECIFIED):
        """ Prep variables """
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.grib_processor = GribFileProcessor(station_source)
        self.model_type: ModelEnum = model_type
        # projection depends on model type
        if self.model_type == ModelEnum.GFS:
            self.projection = ProjectionEnum.GFS_LONLAT
        elif self.model_type == ModelEnum.NAM:
            self.projection = ProjectionEnum.NAM_POLAR_STEREO

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
                        model_run_timestamp, prediction_timestamp = parse_url_for_timestamps(url, self.model_type)
                        model_info = ModelRunInfo(self.model_type, self.projection,
                                                  model_run_timestamp, prediction_timestamp)
                        # download the file:
                        with tempfile.TemporaryDirectory() as temporary_path:
                            downloaded = download(url, temporary_path,
                                                  'REDIS_CACHE_NOAA', self.model_type.value,
                                                  'REDIS_NOAA_CACHE_EXPIRY')
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
            except Exception as exception:
                self.exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.error('unexpected exception processing %s',
                             url, exc_info=exception)

    def process_model_run(self, model_run_hour, client: Client):
        """ Process a particular model run """
        logger.info('Processing {} model run {}'.format(
            self.model_type, model_run_hour))

        urls = list(get_ecmwf_model_run_download_urls(self.now, model_run_hour, client))

        # Process all the urls.
        self.process_model_run_urls(urls)

        # Having completed processing, check if we're all done.
        with app.db.database.get_write_session_scope() as session:
            if check_if_model_run_complete(session, urls):
                logger.info(
                    '{} model run {}:00 completed with SUCCESS'.format(self.model_type, model_run_hour))

                mark_prediction_model_run_processed(
                    session, self.model_type, self.projection, self.now, model_run_hour)

    def process(self):
        """ Entry point for downloading and processing weather model grib files """
        client = Client()
        for hour in get_ecmwf_model_run_hours():
            try:
                self.process_model_run(hour, client)
            except Exception as exception:
                # We catch and log exceptions, but keep trying to process.
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error(
                    'unexpected exception processing %s model run %s',
                    self.model_type, hour, exc_info=exception)


def process_models(station_source: StationSourceEnum = StationSourceEnum.UNSPECIFIED):
    """ downloading and processing models """
    # set the model type requested based on arg passed via command line
    model_type = ModelEnum(sys.argv[1])
    logger.info('model type %s', model_type)

    # grab the start time.
    start_time = datetime.datetime.now()

    ecmwf = ECMWF(model_type, station_source)
    ecmwf.process()

    # with app.db.database.get_write_session_scope() as session:
    #     # interpolate and machine learn everything that needs interpolating.
    #     model_value_processor = ModelValueProcessor(session, station_source)
    #     model_value_processor.process(model_type)

    # calculate the execution time.
    execution_time = datetime.datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # log some info.
    logger.info('%d downloaded, %d processed in total, time taken %d hours, %d minutes, %d seconds (%s)',
                ecmwf.files_downloaded, ecmwf.files_processed, hours, minutes, seconds,
                execution_time)
    # check if we encountered any exceptions.
    if ecmwf.exception_count > 0:
        # if there were any exceptions, return a non-zero status.
        raise CompletedWithSomeExceptions()
    return ecmwf.files_processed


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
        rc_message = ':poop: Encountered error retrieving {sys.argv[1]} model data from NOAA'
        send_rocketchat_notification(rc_message, exception)
        # Exit with a failure code.
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
