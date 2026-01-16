from datetime import datetime
from typing import Optional
import pytest
from unittest.mock import MagicMock
import weather_model_jobs.env_canada
import weather_model_jobs.utils.process_grib
from wps_shared.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp
import wps_shared.db.database
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_shared.tests.conftest import (
    anyio_backend,
    mock_env,
    mock_aiobotocore_get_session,
    mock_requests,
    mock_redis,
    mock_get_now,
    mock_get_pst_today_start_and_end,
    mock_jwt_decode,
    mock_sentry,
    mock_requests_session,
    mock_client_session,
    spy_access_logging,
    mock_wfwx_api,
)


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """Ensure that all unit tests mock out the database session by default!"""
    monkeypatch.setattr(wps_shared.db.database, "_get_write_session", MagicMock())
    monkeypatch.setattr(wps_shared.db.database, "_get_read_session", MagicMock())

    prediction_model = PredictionModel(
        id=1,
        abbreviation="GDPS",
        projection="latlon.15x.15",
        name="Global Deterministic Prediction System",
    )

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        if model == ModelEnum.GDPS and projection == ProjectionEnum.LATLON_15X_15:
            return prediction_model
        return None

    def mock_get_prediction_run(
        session, prediction_model_id: int, prediction_run_timestamp: datetime
    ):
        return PredictionModelRunTimestamp(
            id=1,
            prediction_model_id=1,
            prediction_run_timestamp=get_utc_now(),
            prediction_model=prediction_model,
            complete=True,
        )

    monkeypatch.setattr(
        weather_model_jobs.env_canada, "get_prediction_model", mock_get_prediction_model
    )
    monkeypatch.setattr(
        weather_model_jobs.utils.process_grib,
        "get_prediction_model",
        mock_get_prediction_model,
    )
    monkeypatch.setattr(
        weather_model_jobs.env_canada, "get_prediction_run", mock_get_prediction_run
    )
