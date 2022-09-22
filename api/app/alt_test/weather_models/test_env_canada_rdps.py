""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import pytest
import requests
from sqlalchemy.orm import Session
import app.utils.time as time_utils
from app.weather_models import env_canada
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp)
import app.db.database
# pylint: disable=unused-import
from app.tests.weather_models.test_env_canada_gdps import (MockResponse, mock_get_stations,
                                                           mock_get_model_run_predictions_for_grid,
                                                           mock_get_actuals_left_outer_join_with_predictions)

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out sqlalchemy session object """

    rdps_prediction_model = PredictionModel(id=2,
                                            abbreviation='RDPS',
                                            projection='ps10km',
                                            name='Regional Deterministic Prediction System')
    rdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=2, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=rdps_prediction_model, complete=True)

    def mock_get_rdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(rdps_prediction_model_run, rdps_prediction_model)]

    monkeypatch.setattr(env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_rdps_prediction_model_run_timestamp_records)


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
    total_num_of_urls = 85 * len(env_canada.GRIB_LAYERS) - 1
    assert len(list(env_canada.get_regional_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_rdps(mock_download,
                      mock_database,
                      mock_get_model_run_predictions_for_grid,
                      mock_get_actuals_left_outer_join_with_predictions,
                      mock_get_stations):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "RDPS"]
    assert env_canada.process_models() == 1

# pylint: enable=unused-import
