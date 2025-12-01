import logging
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import func
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
    WeatherStationModelPrediction,
)
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum

logger = logging.getLogger(__name__)


class ModelRunRepository:
    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        self.session = session

    def get_prediction_run(
        self, prediction_model_id: int, prediction_run_timestamp: datetime
    ) -> PredictionModelRunTimestamp:
        """load the model run from the database (.e.g. for 2020 07 07 12h00)."""
        logger.info("get prediction run for %s", prediction_run_timestamp)
        return (
            self.session.query(PredictionModelRunTimestamp)
            .filter(PredictionModelRunTimestamp.prediction_model_id == prediction_model_id)
            .filter(
                PredictionModelRunTimestamp.prediction_run_timestamp == prediction_run_timestamp
            )
            .first()
        )

    def get_prediction_model(
        self, model_enum: ModelEnum, projection: ProjectionEnum
    ) -> PredictionModel:
        """Get the prediction model corresponding to a particular abbreviation and projection."""
        return (
            self.session.query(PredictionModel)
            .filter(PredictionModel.abbreviation == model_enum.value)
            .filter(PredictionModel.projection == projection.value)
            .first()
        )

    def get_processed_url(self, url: str) -> ProcessedModelRunUrl:
        """Get record corresponding to a processed file."""
        processed_url = (
            self.session.query(ProcessedModelRunUrl).filter(ProcessedModelRunUrl.url == url).first()
        )
        return processed_url

    def mark_url_as_processed(self, url: str):
        """Mark url as processed in the database"""
        processed_url = self.get_processed_url(url)
        if processed_url:
            logger.info("re-processed %s", url)
        else:
            logger.info("file processed %s", url)
            processed_url = ProcessedModelRunUrl(url=url, create_date=get_utc_now())
        processed_url.update_date = get_utc_now()
        self.session.add(processed_url)
        self.session.commit()

    def get_processed_url_count(self, urls: List[str]) -> int:
        """Return the number of matching urls"""
        return (
            self.session.query(ProcessedModelRunUrl)
            .filter(ProcessedModelRunUrl.url.in_(urls))
            .count()
        )

    def check_if_model_run_complete(self, urls: List[str]) -> bool:
        """Check if a particular model run is complete"""
        actual_count = self.get_processed_url_count(urls)
        expected_count = len(urls)
        logger.info("we have processed %s/%s files", actual_count, expected_count)
        return actual_count == expected_count and actual_count > 0

    def create_prediction_run(
        self, prediction_model_id: int, prediction_run_timestamp: datetime
    ) -> PredictionModelRunTimestamp:
        """Create a model prediction run for a particular model."""
        prediction_run = PredictionModelRunTimestamp(
            prediction_model_id=prediction_model_id,
            prediction_run_timestamp=prediction_run_timestamp,
            complete=False,
            interpolated=False,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def get_or_create_prediction_run(
        self, prediction_model: PredictionModel, prediction_run_timestamp: datetime
    ) -> PredictionModelRunTimestamp:
        """Get a model prediction run for a particular model, creating one if it doesn't already exist."""
        prediction_run = self.get_prediction_run(prediction_model.id, prediction_run_timestamp)
        if not prediction_run:
            logger.info(
                "Creating prediction run %s for %s",
                prediction_model.abbreviation,
                prediction_run_timestamp,
            )
            prediction_run = self.create_prediction_run(
                prediction_model.id, prediction_run_timestamp
            )
        return prediction_run

    def mark_prediction_model_run_processed(
        self, model: ModelEnum, projection: ProjectionEnum, model_run_datetime: datetime
    ):
        """Mark a prediction model run as processed (complete)"""
        prediction_model = self.get_prediction_model(model, projection)
        logger.info(
            "prediction_model:%s, prediction_run_timestamp:%s", prediction_model, model_run_datetime
        )
        prediction_run = self.get_prediction_run(prediction_model.id, model_run_datetime)
        logger.info("prediction run: %s", prediction_run)
        prediction_run.complete = True
        self.session.add(prediction_run)
        self.session.commit()

    def store_model_run_prediction(self, prediction: ModelRunPrediction):
        """Store the model run prediction in the database."""
        self.session.add(prediction)
        self.session.commit()

    def get_model_run_prediction(
        self,
        prediction_run: PredictionModelRunTimestamp,
        prediction_timestamp: datetime,
        station_code: int,
    ) -> ModelRunPrediction:
        prediction = (
            self.session.query(ModelRunPrediction)
            .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_run.id)
            .filter(ModelRunPrediction.prediction_timestamp == prediction_timestamp)
            .filter(ModelRunPrediction.station_code == station_code)
            .first()
        )
        return prediction

    def get_prediction_model_run_timestamp_records(
        self, model_type: ModelEnum, complete: bool = True, interpolated: bool = True
    ) -> List[Tuple[PredictionModelRunTimestamp, PredictionModel]]:
        """Get prediction model run timestamps (filter on complete and interpolated if provided.)"""
        query = (
            self.session.query(PredictionModelRunTimestamp, PredictionModel)
            .join(
                PredictionModelRunTimestamp,
                PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id,
            )
            .filter(PredictionModel.abbreviation == model_type.value)
            .filter(PredictionModelRunTimestamp.interpolated == interpolated)
            .filter(PredictionModelRunTimestamp.complete == complete)
            .order_by(PredictionModelRunTimestamp.prediction_run_timestamp)
        )
        return query.all()

    def get_weather_station_model_prediction(
        self,
        station_code: int,
        prediction_model_run_timestamp_id: int,
        prediction_timestamp: datetime,
    ) -> WeatherStationModelPrediction:
        """Get the model prediction for a weather station given a model run and a timestamp."""
        return (
            self.session.query(WeatherStationModelPrediction)
            .filter(WeatherStationModelPrediction.station_code == station_code)
            .filter(
                WeatherStationModelPrediction.prediction_model_run_timestamp_id
                == prediction_model_run_timestamp_id
            )
            .filter(WeatherStationModelPrediction.prediction_timestamp == prediction_timestamp)
            .first()
        )

    def get_accumulated_precipitation(
        self, station_code: int, start_datetime: datetime, end_datetime: datetime
    ):
        """Get the accumulated precipitation for a station by datetime range."""
        stmt = select(func.sum(HourlyActual.precipitation)).where(
            HourlyActual.station_code == station_code,
            HourlyActual.weather_date > start_datetime,
            HourlyActual.weather_date <= end_datetime,
        )
        result = self.session.scalars(stmt).first()
        if result is None:
            return 0
        return result

    def get_model_run_predictions_for_station(
        self, station_code: int, prediction_run: PredictionModelRunTimestamp
    ) -> List[ModelRunPrediction]:
        """Get all the predictions for a provided model run"""
        logger.info("Getting model predictions for grid %s", prediction_run)
        return (
            self.session.query(ModelRunPrediction)
            .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_run.id)
            .filter(ModelRunPrediction.station_code == station_code)
            .order_by(ModelRunPrediction.prediction_timestamp)
            .all()
        )

    def store_weather_station_model_prediction(self, prediction: WeatherStationModelPrediction):
        """Store the model run prediction in the database."""
        prediction.update_date = get_utc_now()
        self.session.add(prediction)
        # we need to flush so that added prediction are available for later queries, especially 24 hour precip
        self.session.flush()

    def mark_model_run_interpolated(self, model_run: PredictionModelRunTimestamp):
        """Having completely processed a model run, we can mark it has having been interpolated."""
        model_run.interpolated = True
        logger.info("marking %s as interpolated", model_run)
        self.session.add(model_run)
        self.session.commit()
