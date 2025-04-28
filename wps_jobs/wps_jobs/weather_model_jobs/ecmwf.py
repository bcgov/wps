import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from herbie import Herbie
import asyncio
from osgeo import gdal
from pyproj import CRS, Transformer

from wps_shared.geospatial.geospatial import NAD83_CRS, get_transformer
import wps_shared.utils.time as time_utils
from wps_shared.schemas.stations import WeatherStation
from wps_shared.wps_logging import configure_logging
from wps_shared.stations import get_stations_asynchronously
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_jobs.weather_model_jobs import ModelEnum, ModelRunInfo, ModelRunProcessResult, ProjectionEnum
from wps_jobs.weather_model_jobs.ecmwf_model_processor import ECMWFModelProcessor, TEMP
from wps_jobs.weather_model_jobs.utils.process_grib import PredictionModelNotFound
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModelRunTimestamp

gdal.UseExceptions()

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


def get_stations_dataframe(transformer: Transformer, stations: List[WeatherStation]) -> pd.DataFrame:
    stations_df = pd.DataFrame([station.model_dump(include={"code", "name", "lat", "long"}) for station in stations]).rename(columns={"lat": "latitude", "long": "longitude"})

    stations_df[["longitude", "latitude"]] = stations_df.apply(
        lambda row: transformer.transform(row["longitude"], row["latitude"]),
        axis=1,
        result_type="expand",
    )
    return stations_df


def get_ecmwf_transformer(working_dir: str, herbie_instance: Herbie) -> Transformer:
    grib = herbie_instance.download(TEMP, verbose=False, save_dir=working_dir)  # Any variable can be used to get the model projection
    dataset = gdal.Open(grib)

    wkt = dataset.GetProjection()
    crs = CRS.from_string(wkt)
    transformer = get_transformer(NAD83_CRS, crs)

    dataset = None
    os.remove(grib)
    return transformer


class ECMWF:
    def __init__(self, working_directory: str, stations: List[WeatherStation], model_run_repository: ModelRunRepository):
        self.now = time_utils.get_utc_now()
        self.model_type = ModelEnum.ECMWF
        self.projection = ProjectionEnum.ECMWF_LATLON
        self.working_directory = working_directory
        self.model_run_repository = model_run_repository
        self.stations = stations
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        self.ecmwf_processor = ECMWFModelProcessor(working_directory)

    def process_model_run(self, model_run_hour) -> List[ModelRunProcessResult]:
        """Process a particular model run"""
        logger.info("Processing {} model run {:02d}".format(self.model_type, model_run_hour))

        model_datetime = self.now.replace(hour=model_run_hour, minute=0, second=0, microsecond=0)

        self.prediction_model = self.model_run_repository.get_prediction_model(self.model_type, self.projection)
        if not self.prediction_model:
            raise PredictionModelNotFound("Could not find this prediction model in the database", self.model_type, self.projection)

        prediction_run = self.model_run_repository.get_or_create_prediction_run(self.prediction_model, model_datetime)
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
                    transformer = get_ecmwf_transformer(self.working_directory, H)
                    stations_df = get_stations_dataframe(transformer, self.stations)
                    process_result = self.ecmwf_processor.process_grib_data(H, model_info, stations_df)
                    self.store_processed_result(self.stations, prediction_run, process_result)
                except Exception as exception:
                    self.exception_count += 1
                    # We intentionally catch a broad exception, as we want to try and download as much
                    # as we can.
                    logger.error("unexpected exception processing %s", url, exc_info=exception)
                self.files_processed += 1

    def process(self):
        for hour in get_model_run_hours(self.model_type):
            try:
                self.process_model_run(hour)
            except Exception as exception:
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error("unexpected exception processing %s model run %d", self.model_type, hour, exc_info=exception)

    def store_processed_result(self, stations: List[WeatherStation], prediction_run: PredictionModelRunTimestamp, process_result: ModelRunProcessResult):
        for station in stations:
            prediction = self.model_run_repository.get_model_run_prediction(prediction_run, process_result.model_run_info.prediction_timestamp, station.code)
            if not prediction:
                prediction = ModelRunPrediction()
                prediction.prediction_model_run_timestamp_id = prediction_run.id
                prediction.prediction_timestamp = process_result.model_run_info.prediction_timestamp
                prediction.station_code = station.code

            station_data = process_result.data.sel(point_code=station.code)

            for field in ModelRunPrediction.get_weather_model_fields():
                if field in station_data:
                    setattr(prediction, field, station_data[field].item())

            self.model_run_repository.store_model_run_prediction(prediction)


async def process_models():
    # grab the start time.
    start_time = datetime.now()
    stations = await get_stations_asynchronously()

    with get_write_session_scope() as session:
        with tempfile.TemporaryDirectory() as temp_dir:
            ecmwf = ECMWF(temp_dir, stations, ModelRunRepository(session))
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
