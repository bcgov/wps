""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import pytest
import requests
from aiohttp import ClientSession
from typing import Optional
from sqlalchemy.orm import Session
from wps_shared.weather_models.job_utils import GRIB_LAYERS, get_regional_model_run_download_urls
import wps_shared.utils.time as time_utils
import wps_jobs.weather_model_jobs.utils.process_grib
import wps_jobs.weather_model_jobs.env_canada
import wps_jobs.weather_model_jobs.common_model_fetchers
import wps_shared.db.crud.weather_models
from wps_shared.db.models.weather_models import PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp
from wps_shared.tests.common import default_mock_client_get
from tests.weather_models.test_env_canada_gdps import MockResponse

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    rdps_url = ('https://dd.weather.gc.ca/model_gem_regional/10km/grib2/00/034/'
                'CMC_reg_RH_TGL_2_ps10km_2020052100_P034.grib2')
    rdps_processed_model_run = ProcessedModelRunUrl(url=rdps_url)
    rdps_prediction_model = PredictionModel(id=2,
                                            abbreviation='RDPS',
                                            projection='ps10km',
                                            name='Regional Deterministic Prediction System')
    rdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=2, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=rdps_prediction_model, complete=True)

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        return rdps_prediction_model

    def mock_get_rdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(rdps_prediction_model_run, rdps_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != rdps_url:
            return rdps_processed_model_run
        return None

    def mock_get_prediction_run(*args, **kwargs):
        return rdps_prediction_model_run

    monkeypatch.setattr(wps_jobs.weather_model_jobs.utils.process_grib, "get_prediction_model", mock_get_prediction_model)
    monkeypatch.setattr(wps_jobs.weather_model_jobs.common_model_fetchers, "get_prediction_model_run_timestamp_records", mock_get_rdps_prediction_model_run_timestamp_records)
    monkeypatch.setattr(wps_jobs.weather_model_jobs.env_canada, "get_processed_file_record", mock_get_processed_file_record)
    monkeypatch.setattr(wps_shared.db.crud.weather_models, "get_prediction_run", mock_get_prediction_run)


@pytest.fixture()
def mock_get_processed_file_record(monkeypatch):
    """ Mock "get_processed_file_record" to only return the None on the 1st call. """
    called = False

    def get_processed_file_record(session: Session, url: str):
        nonlocal called
        if called:
            return ProcessedModelRunUrl()
        called = True
        return None

    monkeypatch.setattr(wps_jobs.weather_model_jobs.env_canada, "get_processed_file_record", get_processed_file_record)


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get_rdps(*args, **kwargs):
        """ mock env_canada download method for RDPS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_rdps)


@pytest.fixture()
def mock_download_fail(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        return MockResponse(status_code=400)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


def test_get_rdps_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    # -1 because 000 hour has no APCP_SFC_0
    total_num_of_urls = 85 * len(GRIB_LAYERS) - 1
    assert len(list(get_regional_model_run_download_urls(time_utils.get_utc_now(), 0))) == total_num_of_urls


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_rdps(mock_download, mock_database, monkeypatch: pytest.MonkeyPatch):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "RDPS"]
    assert wps_jobs.weather_model_jobs.env_canada.process_models() == 1
