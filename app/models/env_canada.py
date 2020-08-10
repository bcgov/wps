""" A script that downloads weather models from Environment Canada HTTP data server
TODO: Move this file to app/models/ (not part of this PR as it makes comparing prev. version difficult -
      there are so many changes, it's picked up as a delete instead of a move.)
"""

import os
import sys
import json
import datetime
import logging
import logging.config
import time
import tempfile
import requests
import app.db.database
from app.db.crud import get_processed_file_record
from app.db.models import ProcessedModelRunFile
from app.models.process_grib import GribFileProcessor, ModelRunInfo


# If running as it's own process, configure loggin appropriately.
if __name__ == "__main__":
    LOGGING_CONFIG = os.path.join(os.path.dirname(__file__), '../logging.json')
    if os.path.exists(LOGGING_CONFIG):
        with open(LOGGING_CONFIG) as config_file:
            CONFIG = json.load(config_file)
        logging.config.dictConfig(CONFIG)

logger = logging.getLogger(__name__)


class UnhandledPredictionModelType(Exception):
    """ Exception raised when an unknown model type is encountered. """


# pylint: disable=too-many-locals
def parse_env_canada_filename(filename):
    """ Take a grib filename, as per file name nomenclature defined at
    https://weather.gc.ca/grib/grib2_glb_25km_e.html, and parse into a meaningful object.
    """

    base = os.path.basename(filename)
    parts = base.split('_')
    model = parts[1]
    variable = parts[2]
    level_type = parts[3]
    level = parts[4]
    variable_name = '_'.join(
        [variable, level_type, level])
    projection = parts[5]
    forecast_start = parts[6][:-2]
    run_time = parts[6][-2:]
    model_run_timestamp = datetime.datetime(
        year=int(forecast_start[:4]),
        month=int(forecast_start[4:6]),
        day=int(forecast_start[6:8]),
        hour=int(run_time), tzinfo=datetime.timezone.utc)
    last_part = parts[7].split('.')
    forecast_hour = last_part[0][1:]
    forecast_timestamp = model_run_timestamp + \
        datetime.timedelta(hours=int(forecast_hour))

    if model == 'glb':
        model_abbreviation = 'GDPS'
    elif model == 'reg':
        model_abbreviation = 'RDPS'
    else:
        raise UnhandledPredictionModelType(
            'Unhandeled prediction model type found', model)

    info = ModelRunInfo()
    info.model_abbreviation = model_abbreviation
    info.projection = projection
    info.model_run_timestamp = model_run_timestamp
    info.forecast_timestamp = forecast_timestamp
    info.variable_name = variable_name
    return info


def get_file_date_part(now, hour) -> str:
    """ Construct the part of the filename that contains the model run date
    """
    if now.hour < hour:
        # if now (e.g. 10h00) is less than model run (e.g. 12), it means we have to look for yesterdays
        # model run.
        day = now.day - 1
    else:
        day = now.day
    date = '{year}{month:02d}{day:02d}'.format(
        year=now.year, month=now.month, day=day)
    return date


def get_utcnow():
    """ Wrapped datetime.datetime.uctnow() for easier mocking in unit tests.
    """
    return datetime.datetime.utcnow()


def get_download_urls():
    """ Create a list of urls to download and return it """
    # We always work in UTC:
    now = get_utcnow()

    # hh: model run start, in UTC [00, 12]
    # hhh: forecast hour [000, 003, 006, ..., 240]
    # pylint: disable=invalid-name
    for hour in [0, 12]:
        hh = '{:02d}'.format(hour)
        # For the global model, we have prediction at 3 hour intervals up to 240 hours.
        for h in range(0, 241, 3):
            hhh = format(h, '03d')
            for level in ['TMP_TGL_2', 'RH_TGL_2']:
                base_url = 'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{}/{}/'.format(
                    hh, hhh)
                date = get_file_date_part(now, hour)
                filename = 'CMC_glb_{}_latlon.15x.15_{}{}_P{}.grib2'.format(
                    level, date, hh, hhh)
                url = base_url + filename
                yield url, filename


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
    logger.info('downloading %s', url)
    response = requests.get(url)
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


def flag_file_as_processed(session, url):
    """ Flag the file as processed in the database """
    processed_file = get_processed_file_record(session, url)
    if processed_file:
        logger.info('re-procesed %s', url)
    else:
        logger.info('file processed %s', url)
        processed_file = ProcessedModelRunFile(
            url=url,
            create_date=datetime.datetime.now(datetime.timezone.utc))
    processed_file.update_date = datetime.datetime.now(datetime.timezone.utc)
    session.add(processed_file)
    session.commit()


def main():
    """ main script """
    start_time = time.time()
    session = app.db.database.get_session()
    files_downloaded = 0
    files_processed = 0
    exception_count = 0
    urls = get_download_urls()
    processor = GribFileProcessor()
    with tempfile.TemporaryDirectory() as gdps_path:

        for url, filename in urls:
            try:
                # check the database for a record of this file:
                processed_file_record = get_processed_file_record(session, url)
                if processed_file_record:
                    # This file has already been processed - so we skip it.
                    logger.info('file aready processed %s', url)
                else:
                    # extract model info from filename:
                    model_info = parse_env_canada_filename(filename)
                    # download the file:
                    downloaded = download(url, gdps_path)
                    if downloaded:
                        files_downloaded += 1
                        # If we've downloaded the file ok, we can now process it.
                        try:
                            processor.process_grib_file(downloaded, model_info)
                            # Flag the file as processed
                            flag_file_as_processed(session, url)
                            files_processed += 1
                        finally:
                            # delete the file when done.
                            os.remove(downloaded)
            # pylint: disable=broad-except
            except Exception as exception:
                exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.error('unexpected exception processing %s',
                             url, exc_info=exception)

    execution_time = round(time.time() - start_time, 1)
    logger.info('%d downloaded, %d processed in total, took %s seconds',
                files_downloaded, files_processed, execution_time)
    if exception_count > 0:
        logger.warning('completed processing with some exceptions')
        sys.exit(os.EX_SOFTWARE)
    return files_processed


if __name__ == "__main__":
    main()
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)
