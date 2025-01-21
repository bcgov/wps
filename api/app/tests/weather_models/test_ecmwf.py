import logging
from typing import Optional

import pytest
from aiohttp import ClientSession
from sqlalchemy.orm import Session

import app.db.crud.weather_models
import app.db.database
import app.jobs.common_model_fetchers
import app.jobs.ecmwf
import app.jobs.env_canada
import app.utils.time as time_utils
import app.weather_models.process_grib
from app.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp, ProcessedModelRunUrl
from app.tests.common import default_mock_client_get
from app.tests.weather_models.test_process_grib_herbie import mock_herbie_download_grib, mock_herbie_find_grib

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_database(monkeypatch):
    """Mocked out database queries"""
    ecmwf_url = 'https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20250114/00z/ifs/0p25/oper/20250114000000-0h-oper-fc.grib2'
    ecmwf_processed_model_run = ProcessedModelRunUrl(url=ecmwf_url)
    ecmwf_prediction_model = PredictionModel(id=3, abbreviation='ECMWF', projection='latlon.0.25deg', name='ECMWF Integrated Forecast System')
    ecmwf_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=ecmwf_prediction_model.id, prediction_run_timestamp=time_utils.get_utc_now(), prediction_model=ecmwf_prediction_model, complete=True
    )

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        return ecmwf_prediction_model

    def mock_get_ecmwf_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(ecmwf_prediction_model_run, ecmwf_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != ecmwf_url:
            return ecmwf_processed_model_run
        return None

    def mock_get_prediction_run(*args, **kwargs):
        return ecmwf_prediction_model_run

    monkeypatch.setattr(app.weather_models.process_grib, 'get_prediction_model', mock_get_prediction_model)
    monkeypatch.setattr(app.jobs.common_model_fetchers, 'get_prediction_model_run_timestamp_records', mock_get_ecmwf_prediction_model_run_timestamp_records)
    monkeypatch.setattr(app.jobs.env_canada, 'get_processed_file_record', mock_get_processed_file_record)
    monkeypatch.setattr(app.db.crud.weather_models, 'get_prediction_run', mock_get_prediction_run)


@pytest.fixture()
def mock_get_processed_file_record(monkeypatch):
    """Mock "get_processed_file_record" to only return the None on the 1st call."""
    called = False

    def get_processed_file_record(session: Session, url: str):
        nonlocal called
        if called:
            return ProcessedModelRunUrl()
        called = True
        return None

    monkeypatch.setattr(app.jobs.ecmwf, 'get_processed_file_record', get_processed_file_record)


def test_ecmwf_number_of_files():
    num_files = len(list(app.jobs.ecmwf.get_ecmwf_forecast_hours()))

    assert num_files == 65


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_ecmwf_run_complete(mock_database, monkeypatch: pytest.MonkeyPatch):
    """run process method to see if it runs successfully."""
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    assert app.jobs.ecmwf.process_models() == 0
