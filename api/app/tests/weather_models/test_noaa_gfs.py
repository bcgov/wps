""" Unit tests for app/jobs/noaa.py """

import os
import logging
from datetime import datetime, timezone
from app.jobs import common_model_fetchers
from app.tests.weather_models.test_models_common import MockResponse, shape, mock_get_model_run_predictions
import app.utils.time as time_utils
import pytest
import requests
from geoalchemy2.shape import from_shape
from app.db.models.weather_models import (PredictionModel,
                                          PredictionModelGridSubset, PredictionModelRunTimestamp,
                                          ProcessedModelRunUrl)
from app.jobs import noaa
import app.db.crud.weather_models


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_get_model_run_predictions_for_grid(monkeypatch):
    """ Mock out call to DB returning predictions """

    monkeypatch.setattr(
        common_model_fetchers, 'get_model_run_predictions_for_grid', mock_get_model_run_predictions)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    gfs_url = ('https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-004-0.5-degree/'
               'forecast/202302/20230219/gfs_4_20230219_0600_018.grb2')
    gfs_processed_model_run = ProcessedModelRunUrl(url=gfs_url)
    gfs_prediction_model = PredictionModel(id=1,
                                           abbreviation='GFS',
                                           projection='lonlat.0.5deg',
                                           name='Global Forecast System')
    gfs_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=gfs_prediction_model, complete=True)

    def mock_get_gfs_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(gfs_prediction_model_run, gfs_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != gfs_url:
            return gfs_processed_model_run
        return None

    def mock_get_grids_for_coordinate(session, prediction_model, coordinate):
        return [PredictionModelGridSubset(
            id=1, prediction_model_id=gfs_prediction_model.id, geom=from_shape(shape)), ]

    def mock_get_prediction_run(*args, **kwargs):
        return gfs_prediction_model_run

    monkeypatch.setattr(noaa, 'get_processed_file_record', mock_get_processed_file_record)
    monkeypatch.setattr(common_model_fetchers, 'get_prediction_model_run_timestamp_records',
                        mock_get_gfs_prediction_model_run_timestamp_records)
    monkeypatch.setattr(common_model_fetchers, 'get_grids_for_coordinate', mock_get_grids_for_coordinate)
    monkeypatch.setattr(app.db.crud.weather_models, 'get_prediction_run', mock_get_prediction_run)


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for NOAA download """
    def mock_requests_get_gfs(*args, **kwargs):
        """ mock common_model_fetchers download method for GFS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'gfs_4_20230219_0600_018.grb2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_gfs)


def test_get_gfs_model_run_download_urls_for_0000_utc():
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future
    expected_num_of_urls = 2 * 11
    assert len(list(noaa.get_gfs_model_run_download_urls(time_utils.get_utc_now(), '0000'))) == expected_num_of_urls


def test_get_gfs_model_run_download_urls_for_0600_utc():
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future (11 days total incl. today)
    expected_num_of_urls = 2 * 11
    assert len(list(noaa.get_gfs_model_run_download_urls(time_utils.get_utc_now(), '0600'))) == expected_num_of_urls


def test_parse_url_for_timestamps_simple():
    """ simple test case for noaa.parse_url_for_timestamps(): model_run_timestamp and prediction_timestamp
    are on the same day """
    url = 'https://example.com/model/gfs_4_20230221_0600_012.grb2'
    expected_model_run_timestamp = datetime(2023, 2, 21, 6, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 2, 21, 18, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp


def test_parse_url_for_timestamps_complex():
    """ more complex test case for noaa.parse_url_for_timestamps(): model_run_timestamp and
    prediction_timestamp are on different days """
    url = 'https://example.com/model/gfs_4_20230221_0600_039.grb2'
    expected_model_run_timestamp = datetime(2023, 2, 21, 6, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 2, 22, 21, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp
