from datetime import datetime
import pytest
from typing import Optional
from unittest.mock import MagicMock
import wps_shared.db.database
from wps_shared.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum
import wps_jobs.weather_model_jobs.env_canada
import wps_jobs.weather_model_jobs.utils.process_grib

@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """Ensure that all unit tests mock out the database session by default!"""
    monkeypatch.setattr(wps_shared.db.database, "_get_write_session", MagicMock())
    monkeypatch.setattr(wps_shared.db.database, "_get_read_session", MagicMock())

    prediction_model = PredictionModel(id=1, abbreviation="GDPS", projection="latlon.15x.15", name="Global Deterministic Prediction System")

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        if model == ModelEnum.GDPS and projection == ProjectionEnum.LATLON_15X_15:
            return prediction_model
        return None

    def mock_get_prediction_run(session, prediction_model_id: int, prediction_run_timestamp: datetime):
        return PredictionModelRunTimestamp(id=1, prediction_model_id=1, prediction_run_timestamp=get_utc_now(), prediction_model=prediction_model, complete=True)

    monkeypatch.setattr(wps_jobs.weather_model_jobs.env_canada, "get_prediction_model", mock_get_prediction_model)
    monkeypatch.setattr(wps_jobs.weather_model_jobs.utils.process_grib, "get_prediction_model", mock_get_prediction_model)
    monkeypatch.setattr(wps_jobs.weather_model_jobs.env_canada, "get_prediction_run", mock_get_prediction_run)