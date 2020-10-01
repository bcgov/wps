""" Unit tests for app/env_canada.py """

import os
import logging
import datetime
from datetime import datetime
import pytest
import requests
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.time_utils as time_utils
import app.db.database
from app.schemas import WeatherStation, Season
from app.models import env_canada, machine_learning
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           PredictionModelGridSubset, ModelRunGridSubsetPrediction)
from app.tests.models.crud import get_actuals_left_outer_join_with_predictions
# pylint: disable=unused-argument, redefined-outer-name


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
def mock_get_model_run_predictions_for_grid(monkeypatch):
    """ Mock out call to DB returning predictions """
    def mock_get(*args):
        result = [
            ModelRunGridSubsetPrediction(
                tmp_tgl_2=[2, 3, 4, 5],
                rh_tgl_2=[10, 20, 30, 40],
                prediction_timestamp=datetime(2020, 10, 10, 18)),
            ModelRunGridSubsetPrediction(
                tmp_tgl_2=[1, 2, 3, 4],
                rh_tgl_2=[20, 30, 40, 50],
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


@ pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session object """
    geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
            " -120.525 50.62500000000001, -120.525 50.77500000000001))")
    shape = shapely.wkt.loads(geom)

    url = ('https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/000/'
           'CMC_glb_TMP_TGL_2_latlon.15x.15_2021020300_P000.grib2')
    processed_model_run = ProcessedModelRunUrl(url=url)

    prediction_model = PredictionModel(id=1,
                                       abbreviation='GDPS',
                                       projection='latlon.15x.15',
                                       name='Global Deterministic Prediction System')
    prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=prediction_model, complete=True)

    def mock_get_session(*args):

        return UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'GDPS',
                                  PredictionModel.projection == 'latlon.15x.15')],
                [prediction_model],
            ),
            (
                [mock.call.query(ProcessedModelRunUrl),
                 mock.call.filter(ProcessedModelRunUrl.url == url)],
                [processed_model_run]
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [prediction_model_run]
            ),
            (
                [mock.call.query(PredictionModelGridSubset)],
                [PredictionModelGridSubset(
                    id=1, prediction_model_id=prediction_model.id, geom=from_shape(shape))]
            )
        ])

    def mock_get_prediction_model_run_timestamp_records(*args, **kwargs):
        return [prediction_model_run, ]

    monkeypatch.setattr(app.db.database, 'get_write_session', mock_get_session)
    monkeypatch.setattr(app.models.env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_prediction_model_run_timestamp_records)


@ pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


@ pytest.fixture()
def mock_download_fail(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        return MockResponse(status_code=400)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


def test_get_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    total_num_of_urls = 81 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(list(env_canada.get_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


def test_main(mock_download,
              mock_session,
              mock_get_processed_file_count,
              mock_get_model_run_predictions_for_grid,
              mock_get_actuals_left_outer_join_with_predictions,
              mock_get_stations):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    assert env_canada.main() == 1


def test_for_zero_day_bug(monkeypatch):
    """ There's a very specific case, where on the 1st day of the new month, before 12 UTC,
    a url with a month day zero is construced.
    This test ensures that if it's before 12 UTC, we look for the previous days 12 UTC model run"""
    problem_date = datetime.fromisoformat('2020-09-01T00:13:58+00:00')
    urls = env_canada.get_model_run_download_urls(problem_date, 12)
    url = next(urls)
    expected_url = ('https://dd.weather.gc.ca/model_gem_global/15km/'
                    'grib2/lat_lon/12/000/CMC_glb_TMP_TGL_2_latlon.'
                    '15x.15_2020083112_P000.grib2')
    assert url == expected_url

# pylint: enable=unused-argument, redefined-outer-name
