""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import datetime
from datetime import datetime
import pytest
import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely import wkt
import app.utils.time as time_utils
from app.schemas.stations import WeatherStation, Season
from app.weather_models import env_canada, machine_learning
import db.crud.weather_models
from db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                       ModelRunGridSubsetPrediction, PredictionModelGridSubset)
from tests.weather_models.crud import get_actuals_left_outer_join_with_predictions


logger = logging.getLogger(__name__)


class MockResponse:
    """ Mocked out request.Response object """

    def __init__(self, status_code, content=None):
        self.status_code = status_code
        self.content = content


@pytest.fixture()
def mock_get_stations(monkeypatch):
    """ Mocked out listing of weather stations """
    def mock_get(*args):
        return [WeatherStation(
            code=123, name='Test', lat=50.7, long=-120.425, ecodivision_name='Test',
            core_season=Season(
                start_month=5, start_day=1, end_month=9, end_day=21)), ]
    monkeypatch.setattr(env_canada, 'get_stations_synchronously', mock_get)


@pytest.fixture()
def mock_get_processed_file_count(monkeypatch):
    """ Mocked out get processed file count """
    def mock_get_count(*args):
        return 162
    monkeypatch.setattr(env_canada, 'get_processed_file_count', mock_get_count)


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
def mock_get_model_run_predictions_for_grid(monkeypatch):
    """ Mock out call to DB returning predictions """
    def mock_get(*args):
        result = [
            ModelRunGridSubsetPrediction(
                tmp_tgl_2=[2, 3, 4, 5],
                rh_tgl_2=[10, 20, 30, 40],
                apcp_sfc_0=[2, 4, 3, 6],
                wdir_tgl_10=[10, 20, 30, 40],
                wind_tgl_10=[1, 2, 3, 4],
                prediction_timestamp=datetime(2020, 10, 10, 18)),
            ModelRunGridSubsetPrediction(
                tmp_tgl_2=[1, 2, 3, 4],
                rh_tgl_2=[20, 30, 40, 50],
                apcp_sfc_0=[3, 6, 3, 4],
                wdir_tgl_10=[280, 290, 300, 310],
                wind_tgl_10=[5, 6, 7, 8],
                prediction_timestamp=datetime(2020, 10, 10, 21)),
            ModelRunGridSubsetPrediction(
                tmp_tgl_2=[1, 2, 3, 4],
                rh_tgl_2=None,
                apcp_sfc_0=[3, 6, 3, 4],
                wdir_tgl_10=[20, 30, 40, 50],
                wind_tgl_10=[4, 3, 2, 1],
                prediction_timestamp=datetime(2020, 10, 10, 21))
        ]
        return result
    monkeypatch.setattr(
        env_canada, 'get_model_run_predictions_for_grid', mock_get)


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_left_outer_join_with_predictions',
                        get_actuals_left_outer_join_with_predictions)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
            " -120.525 50.62500000000001, -120.525 50.77500000000001))")
    shape = wkt.loads(geom)
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

    def mock_get_grids_for_coordinate(session, prediction_model, coordinate):
        return [PredictionModelGridSubset(
            id=1, prediction_model_id=gdps_prediction_model.id, geom=from_shape(shape)), ]

    def mock_get_prediction_run(*args, **kwargs):
        return gdps_prediction_model_run

    monkeypatch.setattr(env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_gdps_prediction_model_run_timestamp_records)
    monkeypatch.setattr(env_canada, 'get_processed_file_record', mock_get_processed_file_record)
    monkeypatch.setattr(env_canada, 'get_grids_for_coordinate', mock_get_grids_for_coordinate)
    monkeypatch.setattr(db.crud.weather_models, 'get_prediction_run', mock_get_prediction_run)


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
    total_num_of_urls = 81 * len(env_canada.GRIB_LAYERS) - 1
    assert len(list(env_canada.get_global_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


@pytest.mark.usefixtures('mock_get_processed_file_record')
def test_process_gdps(mock_download,
                      mock_database,
                      mock_get_processed_file_count,
                      mock_get_model_run_predictions_for_grid,
                      mock_get_actuals_left_outer_join_with_predictions,
                      mock_get_stations):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "GDPS"]
    assert env_canada.process_models() == 1


def test_for_zero_day_bug(monkeypatch):
    """ There's a very specific case, where on the 1st day of the new month, before 12 UTC,
    a url with a month day zero is construced.
    This test ensures that if it's before 12 UTC, we look for the previous days 12 UTC model run"""
    problem_date = datetime.fromisoformat('2020-09-01T00:13:58+00:00')
    urls = env_canada.get_global_model_run_download_urls(problem_date, 12)
    url = next(urls)
    expected_url = ('https://dd.weather.gc.ca/model_gem_global/15km/'
                    'grib2/lat_lon/12/000/CMC_glb_TMP_TGL_2_latlon.'
                    '15x.15_2020083112_P000.grib2')
    assert url == expected_url
