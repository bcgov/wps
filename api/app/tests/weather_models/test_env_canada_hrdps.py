""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import pytest
import requests
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
import app.utils.time as time_utils
import app.db.database
from app.weather_models import env_canada
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp)
from app.tests.weather_models.test_env_canada_gdps import MockResponse


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    hrdps_prediction_model = PredictionModel(id=3, abbreviation='HRDPS', projection='ps2.5km',
                                             name='High Resolution Deterministic Prediction System')
    hrdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=3, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=hrdps_prediction_model, complete=True)

    def mock_get_hrdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(hrdps_prediction_model_run, hrdps_prediction_model)]

    monkeypatch.setattr(app.weather_models.env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_hrdps_prediction_model_run_timestamp_records)


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
    def mock_requests_get_hrdps(*args, **kwargs):
        """ mock env_canada download method for HRDPS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_hrdps_continental_RH_TGL_2_ps2.5km_2020100700_P007-00.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_hrdps)


def test_get_hrdps_download_urls():
    """ test to see if get_download_urls methods gives the correct number of urls """
    # -1 because 000 hour has no APCP_SFC_0
    total_num_of_urls = 49 * len(env_canada.GRIB_LAYERS) - 1
    assert len(list(env_canada.get_high_res_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_hrdps(mock_download, mock_database):
    """ run process method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "HRDPS"]
    assert env_canada.process_models() == 1


def test_main_fail(mocker: MockerFixture, monkeypatch):
    """ Run the main method, check that message is sent to rocket chat, and exit code is EX_SOFTWARE """
    sys.argv = ["argv", "HRDPS"]

    def mock_process_models():
        raise Exception()

    rocket_chat_spy = mocker.spy(env_canada, 'send_rocketchat_notification')
    monkeypatch.setattr(env_canada, 'process_models', mock_process_models)

    with pytest.raises(SystemExit) as excinfo:
        env_canada.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
