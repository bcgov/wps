import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from herbie import Herbie
from sqlalchemy.orm import Session

import app.db.database
import app.utils.time as time_utils
from app import configure_logging
from app.db.crud.weather_models import get_or_create_prediction_run, get_prediction_model, get_prediction_run, get_processed_file_record, update_prediction_run
from app.jobs.common_model_fetchers import CompletedWithSomeExceptions, ModelValueProcessor, check_if_model_run_complete, flag_file_as_processed
from app.weather_models import ModelEnum, ProjectionEnum
from app.weather_models.process_grib import ModelRunInfo, PredictionModelNotFound
from app.weather_models.process_grib_herbie import HerbieGribProcessor

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def get_model_run_hours(model_type: ModelEnum):
    """Yield model run hours for model"""
    if model_type == ModelEnum.ECMWF:
        for hour in [0, 12]:
            yield hour


def get_ecmwf_forecast_hours():
    # Yield hours from 0 to 144 by 3-hour intervals
    for h in range(0, 145, 3):
        yield h
    # Yield hours from 150 to 240 by 6-hour intervals
    for h in range(150, 241, 6):
        yield h


def mark_prediction_model_run_processed(session: Session, model: ModelEnum, projection: ProjectionEnum, model_run_datetime: datetime):
    """Mark a prediction model run as processed (complete)"""

    prediction_model = get_prediction_model(session, model, projection)
    logger.info("prediction_model:%s, prediction_run_timestamp:%s", prediction_model, model_run_datetime)
    prediction_run = get_prediction_run(session, prediction_model.id, model_run_datetime)
    logger.info("prediction run: %s", prediction_run)
    prediction_run.complete = True
    update_prediction_run(session, prediction_run)


class ECMWF:
    def __init__(self, session: Session, working_directory: str):
        self.now = time_utils.get_utc_now()
        self.session = session
        self.model_type = ModelEnum.ECMWF
        self.projection = ProjectionEnum.ECMWF_LATLON
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        self.grib_processor = HerbieGribProcessor(working_directory)

    def process_model_run(self, model_run_hour):
        """Process a particular model run"""
        logger.info("Processing {} model run {:02d}".format(self.model_type, model_run_hour))
        processed_urls = []

        model_datetime = self.now.replace(hour=model_run_hour, minute=0, second=0, microsecond=0)

        self.prediction_model = get_prediction_model(self.session, self.model_type, self.projection)
        if not self.prediction_model:
            raise PredictionModelNotFound("Could not find this prediction model in the database", self.model_type, self.projection)

        prediction_run = get_or_create_prediction_run(self.session, self.prediction_model, model_datetime)
        if prediction_run.complete:
            logger.info(f"Prediction run {model_datetime} already completed")
            return

        for prediction_hour in get_ecmwf_forecast_hours():
            model_info = ModelRunInfo(
                model_enum=self.model_type,
                model_run_timestamp=model_datetime,
                prediction_timestamp=model_datetime + timedelta(hours=prediction_hour),
                projection=self.projection,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                H = Herbie(model_datetime.strftime("%Y-%m-%d %H"), model="ifs", product="oper", priority="aws", fxx=prediction_hour, save_dir=temp_dir, verbose=False)
                url = H.grib
                if not url:
                    logger.info(f"grib file not found for {model_info.prediction_timestamp} ")
                    continue

                self.files_downloaded += 1

                try:
                    processed_file_record = get_processed_file_record(self.session, url)
                    if processed_file_record:
                        logger.info(f"file already processed {url}")
                    else:
                        logger.info(f"processing {url}")
                        self.grib_processor.process_grib_file(H, model_info, prediction_run, self.session)
                        # Flag the file as processed
                        flag_file_as_processed(url, self.session)
                        self.files_processed += 1
                    processed_urls.append(url)

                except Exception as exception:
                    self.exception_count += 1
                    # We intentionally catch a broad exception, as we want to try and download as much
                    # as we can.
                    logger.error("unexpected exception processing %s", url, exc_info=exception)

        expected_file_count = len(list(get_ecmwf_forecast_hours()))
        if check_if_model_run_complete(self.session, processed_urls, expected_file_count):
            logger.info("{} model run {:02d}:00 completed with SUCCESS".format(self.model_type, model_run_hour))

            mark_prediction_model_run_processed(self.session, self.model_type, self.projection, model_datetime)

    def process(self):
        for hour in get_model_run_hours(self.model_type):
            try:
                self.process_model_run(0)
            except Exception as exception:
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error("unexpected exception processing %s model run %d", self.model_type, hour, exc_info=exception)


def process_models():
    # grab the start time.
    start_time = datetime.now()

    with app.db.database.get_write_session_scope() as session, tempfile.TemporaryDirectory() as temp_dir:
        ecmwf = ECMWF(session, temp_dir)
        ecmwf.process()

        # interpolate and machine learn everything that needs interpolating.
        model_value_processor = ModelValueProcessor(session)
        model_value_processor.process(ModelEnum.ECMWF)

    # calculate the execution time.
    execution_time = datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    logger.info(f"{ecmwf.files_processed} files processed, time taken {hours} hours, {minutes} minutes, {seconds} seconds")


def main():
    try:
        process_models()
    except CompletedWithSomeExceptions:
        logger.warning("completed processing with some exceptions")
        sys.exit(os.EX_SOFTWARE)
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
