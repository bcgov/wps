import asyncio
import logging
import math
import os
from datetime import datetime
from typing import List

import numpy as np
import wps_nwp as nwp
import wps_shared.utils.time as time_utils
from weather_model_jobs import (
    ModelEnum,
    ModelRunInfo,
    ModelRunProcessResult,
    ProjectionEnum,
)
from weather_model_jobs.ecmwf_hours import get_ecmwf_forecast_hours
from weather_model_jobs.ecmwf_model_processor import VARIABLES, station_values
from weather_model_jobs.ecmwf_prediction_processor import ECMWFPredictionProcessor
from weather_model_jobs.utils.process_grib import PredictionModelNotFound
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModelRunTimestamp
from wps_shared.schemas.stations import WeatherStation
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import get_stations_asynchronously

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def get_model_run_hours(model_type: ModelEnum):
    """Yield model run hours for model"""
    if model_type == ModelEnum.ECMWF:
        for hour in [0, 12]:
            yield hour


def get_forecast_url(model_datetime: datetime, prediction_hour: int) -> str:
    """
    The address of a forecast hour's GRIB file, which is what we record once it is processed.

    It is always the address on the first mirror, whichever mirror the data ends up coming
    from, so that an hour is recognised as processed on later runs.
    """
    return nwp.IFS.url(nwp.IFS.mirrors[0], model_datetime, prediction_hour)


class ECMWF:
    def __init__(
        self,
        client: nwp.Client,
        stations: List[WeatherStation],
        model_run_repository: ModelRunRepository,
    ):
        self.now = time_utils.get_utc_now()
        self.model_type = ModelEnum.ECMWF
        self.projection = ProjectionEnum.ECMWF_LATLON
        self.client = client
        self.model_run_repository = model_run_repository
        self.stations = stations
        self.station_lats = np.array([station.lat for station in stations])
        self.station_lons = np.array([station.long for station in stations])
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0

    async def _process_forecast(
        self,
        fields: List[nwp.Field],
        url: str,
        prediction_run: PredictionModelRunTimestamp,
    ):
        model_info = ModelRunInfo(
            model_enum=self.model_type,
            model_run_timestamp=fields[0].run,
            prediction_timestamp=fields[0].valid_time,
            projection=self.projection,
        )
        data = await station_values(fields, self.station_lats, self.station_lons)
        self.store_processed_result(
            prediction_run, ModelRunProcessResult(model_run_info=model_info, url=url, data=data)
        )

    async def process_model_run(self, model_run_hour):
        """Process a particular model run"""
        self.files_downloaded = 0
        self.files_processed = 0
        logger.info("Processing {} model run {:02d}".format(self.model_type, model_run_hour))

        model_datetime = self.now.replace(hour=model_run_hour, minute=0, second=0, microsecond=0)

        if model_datetime > self.now:
            logger.info(f"Model run {model_datetime} is in the future. Exiting model run.")
            return

        self.prediction_model = self.model_run_repository.get_prediction_model(
            self.model_type, self.projection
        )
        if not self.prediction_model:
            raise PredictionModelNotFound(
                "Could not find this prediction model in the database",
                self.model_type,
                self.projection,
            )

        prediction_run = self.model_run_repository.get_or_create_prediction_run(
            self.prediction_model, model_datetime
        )
        if prediction_run.complete:
            logger.info(f"Prediction run {model_datetime} already completed")
            return

        prediction_hours = list(get_ecmwf_forecast_hours())
        urls = {hour: get_forecast_url(model_datetime, hour) for hour in prediction_hours}

        pending_hours = []
        for hour in prediction_hours:
            if self.model_run_repository.get_processed_url(urls[hour]):
                logger.info(f"file already processed -- {urls[hour]}")
                self.files_processed += 1
            else:
                pending_hours.append(hour)

        # Hours that are not published yet are left out of the stream rather than raising, and
        # are picked up by a later run of this job.
        async for fields in self.client.stream(
            nwp.IFS, model_datetime, pending_hours, VARIABLES, skip_missing=True
        ):
            url = urls[fields[0].step]
            if len(fields) < len(VARIABLES):
                logger.info(f"GRIB file is missing variables, leaving it for a later run -- {url}")
                continue
            self.files_downloaded += 1

            try:
                await self._process_forecast(fields, url, prediction_run)

                self.files_processed += 1
                self.model_run_repository.mark_url_as_processed(url)
            except Exception:
                self.exception_count += 1
                logger.exception("unexpected exception processing %s", url)
                self.model_run_repository.session.rollback()

        # files_processed is incremented whether the file was processed previously or on this run, so we can use it to check if all files were processed.
        if len(prediction_hours) == self.files_processed:
            logger.info(
                f"{self.model_type} model run {model_run_hour:02d}:00 completed with SUCCESS"
            )
            self.model_run_repository.mark_prediction_model_run_processed(
                self.model_type, self.projection, model_datetime
            )
        else:
            logger.info(
                f"{self.model_type} model run {model_run_hour:02d}:00 has "
                f"{self.files_processed} of {len(prediction_hours)} forecast hours processed"
            )

    async def process(self):
        for hour in get_model_run_hours(self.model_type):
            try:
                await self.process_model_run(hour)
            except Exception:
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.exception(
                    "unexpected exception processing %s model run %d",
                    self.model_type,
                    hour,
                )

    def store_processed_result(
        self,
        prediction_run: PredictionModelRunTimestamp,
        process_result: ModelRunProcessResult,
    ):
        # process_result.data holds one value per station, in the order of self.stations
        for index, station in enumerate(self.stations):
            prediction = self.model_run_repository.get_model_run_prediction(
                prediction_run, process_result.model_run_info.prediction_timestamp, station.code
            )
            if not prediction:
                prediction = ModelRunPrediction()
                prediction.prediction_model_run_timestamp_id = prediction_run.id
                prediction.prediction_timestamp = process_result.model_run_info.prediction_timestamp
                prediction.station_code = station.code

            for field in ModelRunPrediction.get_weather_model_fields():
                if field in process_result.data:
                    value = float(process_result.data[field][index])
                    setattr(prediction, field, None if math.isnan(value) else value)

            self.model_run_repository.store_model_run_prediction(prediction)


async def process_models():
    # grab the start time.
    start_time = datetime.now()
    stations = await get_stations_asynchronously()

    with get_write_session_scope() as session:
        model_run_repository = ModelRunRepository(session)
        async with nwp.Client() as client:
            ecmwf = ECMWF(client, stations, model_run_repository)
            await ecmwf.process()

        # interpolate and machine learn everything that needs interpolating.
        ecmwf_prediction_processor = ECMWFPredictionProcessor(stations, model_run_repository)
        ecmwf_prediction_processor.process()

    # calculate the execution time.
    execution_time = datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    logger.info(
        f"{ecmwf.files_processed} files processed, time taken {hours} hours, {minutes} minutes, {seconds} seconds"
    )


def exit_process(code: int):
    # skip Python interpreter cleanup; GDAL/eccodes teardown can segfault in this job.
    os._exit(code)


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_models())
        exit_process(os.EX_OK)
    except Exception as exception:
        logger.exception("An error occurred while processing ECMWF model.")
        rc_message = ":poop: Encountered error retrieving model data from ECMWF"
        send_chatops_notification(rc_message, exception)
        exit_process(os.EX_SOFTWARE)


if __name__ == "__main__":
    main()
