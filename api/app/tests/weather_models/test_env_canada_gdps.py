""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import datetime
from datetime import datetime
import pytest
import requests
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from wps_jobs.wps_jobs.weather_model_jobs import env_canada
from wps_jobs.wps_jobs.weather_model_jobs.env_canada_utils import GRIB_LAYERS, get_global_model_run_download_urls
from wps_jobs.wps_jobs.weather_model_jobs import machine_learning
from wps_jobs.wps_jobs.weather_model_jobs import common_model_fetchers
import wps_shared.utils.time as time_utils
import wps_shared.db.crud.weather_models
from wps_shared.db.models.weather_models import PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp
from app.tests.common import default_mock_client_get
from app.tests.weather_models.crud import get_actuals_left_outer_join_with_predictions
from app.tests.weather_models.test_models_common import (MockResponse, mock_get_processed_file_count, mock_get_stations)

logger = logging.getLogger(__name__)


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

    monkeypatch.setattr(env_canada, 'get_processed_file_record', get_processed_file_record)


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_left_outer_join_with_predictions',
                        get_actuals_left_outer_join_with_predictions)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    gdps_url = ('https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/000/'
                'CMC_glb_TMP_TGL_2_latlon.15x.15_2020052100_P000.grib2')
    gdps_processed_model_run = ProcessedModelRunUrl(url=gdps_url)
    gdps_prediction_model = PredictionModel(id=1,
                                            abbreviation='GDPS',
                                            projection='latlon.15x.15',
                                            name='Global Deterministic Prediction System')
    gdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=gdps_prediction_model, complete=True)

    def mock_get_gdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(gdps_prediction_model_run, gdps_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != gdps_url:
            return gdps_processed_model_run
        return None

    def mock_get_prediction_run(*args, **kwargs):
        return gdps_prediction_model_run

    monkeypatch.setattr(common_model_fetchers, 'get_prediction_model_run_timestamp_records',
                        mock_get_gdps_prediction_model_run_timestamp_records)
    monkeypatch.setattr(common_model_fetchers, 'get_processed_file_record', mock_get_processed_file_record)
    monkeypatch.setattr(wps_shared.db.crud.weather_models, "get_prediction_run", mock_get_prediction_run)


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get_gdps(*args, **kwargs):
        """ mock env_canada download method for GDPS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_gdps)


@pytest.fixture()
def mock_download_fail(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        return MockResponse(status_code=400)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


def test_get_gdps_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    # -1 because 000 hour has no APCP_SFC_0
    total_num_of_urls = 81 * len(GRIB_LAYERS) - 1
    assert len(list(get_global_model_run_download_urls(time_utils.get_utc_now(), 0))) == total_num_of_urls


@pytest.fixture()
def mock_get_processed_file_count(monkeypatch):
    monkeypatch.setattr(wps_shared.db.crud.weather_models, "get_processed_file_count", mock_get_processed_file_count)


@pytest.fixture()
def mock_get_stations_synchronously(monkeypatch):
    monkeypatch.setattr(common_model_fetchers, 'get_stations_synchronously', mock_get_stations)


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_gdps(
    mock_download, mock_database, mock_get_actuals_left_outer_join_with_predictions, mock_get_stations_synchronously, mock_get_processed_file_count, monkeypatch: pytest.MonkeyPatch
):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "GDPS"]
    assert env_canada.process_models() == 1


def test_for_zero_day_bug(monkeypatch):
    """ There's a very specific case, where on the 1st day of the new month, before 12 UTC,
    a url with a month day zero is construced.
    This test ensures that if it's before 12 UTC, we look for the previous days 12 UTC model run"""
    problem_date = datetime.fromisoformat('2020-09-01T00:13:58+00:00')
    urls = get_global_model_run_download_urls(problem_date, 12)
    url = next(urls)
    expected_url = ('https://dd.weather.gc.ca/model_gem_global/15km/'
                    'grib2/lat_lon/12/000/CMC_glb_TMP_TGL_2_latlon.'
                    '15x.15_2020083112_P000.grib2')
    assert url == expected_url
