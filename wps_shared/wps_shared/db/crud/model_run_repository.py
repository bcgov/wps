import logging
from datetime import datetime
from sqlalchemy.orm import Session
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel, PredictionModelRunTimestamp, ProcessedModelRunUrl
from wps_shared.weather_models import ModelEnum, ProjectionEnum

logger = logging.getLogger(__name__)


class ModelRunRepository:
    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        self.session = session

    def get_prediction_run(self, prediction_model_id: int, prediction_run_timestamp: datetime) -> PredictionModelRunTimestamp:
        """load the model run from the database (.e.g. for 2020 07 07 12h00)."""
        logger.info("get prediction run for %s", prediction_run_timestamp)
        return (
            self.session.query(PredictionModelRunTimestamp)
            .filter(PredictionModelRunTimestamp.prediction_model_id == prediction_model_id)
            .filter(PredictionModelRunTimestamp.prediction_run_timestamp == prediction_run_timestamp)
            .first()
        )

    def get_prediction_model(self, model_enum: ModelEnum, projection: ProjectionEnum) -> PredictionModel:
        """Get the prediction model corresponding to a particular abbreviation and projection."""
        return self.session.query(PredictionModel).filter(PredictionModel.abbreviation == model_enum.value).filter(PredictionModel.projection == projection.value).first()

    def get_processed_file_record(self, url: str) -> ProcessedModelRunUrl:
        """Get record corresponding to a processed file."""
        processed_file = self.session.query(ProcessedModelRunUrl).filter(ProcessedModelRunUrl.url == url).first()
        return processed_file

    def create_prediction_run(self, prediction_model_id: int, prediction_run_timestamp: datetime) -> PredictionModelRunTimestamp:
        """Create a model prediction run for a particular model."""
        prediction_run = PredictionModelRunTimestamp(prediction_model_id=prediction_model_id, prediction_run_timestamp=prediction_run_timestamp, complete=False, interpolated=False)
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def get_or_create_prediction_run(self, prediction_model: PredictionModel, prediction_run_timestamp: datetime) -> PredictionModelRunTimestamp:
        """Get a model prediction run for a particular model, creating one if it doesn't already exist."""
        prediction_run = self.get_prediction_run(prediction_model.id, prediction_run_timestamp)
        if not prediction_run:
            logger.info("Creating prediction run %s for %s", prediction_model.abbreviation, prediction_run_timestamp)
            prediction_run = self.create_prediction_run(prediction_model.id, prediction_run_timestamp, False, False)
        return prediction_run

    def mark_prediction_model_run_processed(self, model: ModelEnum, projection: ProjectionEnum, model_run_datetime: datetime):
        """Mark a prediction model run as processed (complete)"""
        prediction_model = self.get_prediction_model(model, projection)
        logger.info("prediction_model:%s, prediction_run_timestamp:%s", prediction_model, model_run_datetime)
        prediction_run = self.get_prediction_run(prediction_model.id, model_run_datetime)
        logger.info("prediction run: %s", prediction_run)
        prediction_run.complete = True
        self.session.add(prediction_run)
        self.session.commit()

    def store_model_run_prediction(self, prediction: ModelRunPrediction):
        """Store the model run prediction in the database."""
        self.session.add(prediction)
        self.session.commit()

    def get_model_run_prediction(self, prediction_run: PredictionModelRunTimestamp, prediction_timestamp: datetime, station_code: int) -> ModelRunPrediction:
        prediction = (
            self.session.query(ModelRunPrediction)
            .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_run.id)
            .filter(ModelRunPrediction.prediction_timestamp == prediction_timestamp)
            .filter(ModelRunPrediction.station_code == station_code)
            .first()
        )
        return prediction
