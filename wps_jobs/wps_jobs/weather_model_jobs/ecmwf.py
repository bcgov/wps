import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import List

from herbie import Herbie
import asyncio

import wps_shared.utils.time as time_utils
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import CompletedWithSomeExceptions
from wps_shared.wps_logging import configure_logging
from wps_shared.stations import get_stations_asynchronously
from wps_jobs.weather_model_jobs import ModelEnum, ModelRunInfo, ProjectionEnum
from wps_jobs.weather_model_jobs.process_grib_herbie import HerbieGribProcessor

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


class ECMWF:
    def __init__(self, working_directory: str, stations: List[WeatherStation]):
        self.now = time_utils.get_utc_now()
        self.model_type = ModelEnum.ECMWF
        self.projection = ProjectionEnum.ECMWF_LATLON
        self.stations = stations
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        self.grib_processor = HerbieGribProcessor(working_directory)

    def process_model_run(self, model_run_hour):
        """Process a particular model run"""
        logger.info("Processing {} model run {:02d}".format(self.model_type, model_run_hour))

        model_datetime = self.now.replace(hour=model_run_hour, minute=0, second=0, microsecond=0)

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
                    station_data = self.grib_processor.process_grib_file(H, model_info, self.stations)
                    logger.info(station_data.head())
                except Exception as exception:
                    self.exception_count += 1
                    # We intentionally catch a broad exception, as we want to try and download as much
                    # as we can.
                    logger.error("unexpected exception processing %s", url, exc_info=exception)

    def process(self):
        for hour in get_model_run_hours(self.model_type):
            try:
                self.process_model_run(12)
            except Exception as exception:
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error("unexpected exception processing %s model run %d", self.model_type, hour, exc_info=exception)


async def process_models():
    # grab the start time.
    start_time = datetime.now()
    stations = await get_stations_asynchronously()

    with tempfile.TemporaryDirectory() as temp_dir:
        ecmwf = ECMWF(temp_dir, stations)
        ecmwf.process()

    # calculate the execution time.
    execution_time = datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    logger.info(f"{ecmwf.files_processed} files processed, time taken {hours} hours, {minutes} minutes, {seconds} seconds")


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_models())
        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing ECMWF model.", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    main()
