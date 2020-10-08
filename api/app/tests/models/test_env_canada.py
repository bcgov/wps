""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import datetime
from datetime import datetime
import app.time_utils as time_utils
import app.db.database
import pytest
import requests
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
from app.models import env_canada
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           PredictionModelGridSubset)
# pylint: disable=unused-argument, redefined-outer-name


logger = logging.getLogger(__name__)


class MockResponse:
    """ Mocked out request.Response object """

    def __init__(self, status_code, content=None):
        self.status_code = status_code
        self.content = content


@pytest.fixture()
def mock_get_processed_file_count(monkeypatch):
    """ Mocked out get processed file count """
    def mock_get_count(*args):
        return 162
    monkeypatch.setattr(env_canada, 'get_processed_file_count', mock_get_count)


@pytest.fixture()
def mock_utcnow(monkeypatch):
    """ Mocked out utcnow, to allow for deterministic tests """
    def mock_get_utcnow(*args):
        return datetime(year=2021, month=2, day=3, hour=0)
    monkeypatch.setattr(env_canada, 'get_utcnow', mock_get_utcnow)


@pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session object """
    geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
            " -120.525 50.62500000000001, -120.525 50.77500000000001))")
    shape = shapely.wkt.loads(geom)

    gdps_url = ('https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/000/'
                'CMC_glb_TMP_TGL_2_latlon.15x.15_2021020300_P000.grib2')
    gdps_processed_model_run = ProcessedModelRunUrl(url=gdps_url)
    gdps_prediction_model = PredictionModel(id=1,
                                            abbreviation='GDPS',
                                            projection='latlon.15x.15',
                                            name='Global Deterministic Prediction System')
    gdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=gdps_prediction_model, complete=True)

    hrdps_url = ('https://dd.weather.gc.ca/model_hrdps/continental/grib2/00/007/CMC_hrdps_continental_TMP_TGL_2_ps2.5km_2020100700_P007-00.grib2')
    hrdps_processed_model_run = ProcessedModelRunUrl(url=hrdps_url)
    hrdps_prediction_model = PredictionModel(id=3, abbreviation='HRDPS', projection='2.5km',
                                             name='High Resolution Deterministic Prediction System')
    hrdps_prediction_model_run = PredictionModelRunTimestamp(
        id=2, prediction_model_id=3, prediction_run_timestamp=time_utils.get_utc_now(), prediction_model=hrdps_prediction_model, complete=True)

    def mock_get_session_gdps(*args):

        return UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'GDPS',
                                  PredictionModel.projection == 'latlon.15x.15')],
                [gdps_prediction_model],
            ),
            (
                [mock.call.query(ProcessedModelRunUrl),
                 mock.call.filter(ProcessedModelRunUrl.url == gdps_url)],
                [gdps_processed_model_run]
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [gdps_prediction_model_run]
            ),
            (
                [mock.call.query(PredictionModelGridSubset)],
                [PredictionModelGridSubset(
                    id=1, prediction_model_id=gdps_prediction_model.id, geom=from_shape(shape))]
            )
        ])

    def mock_get_gdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [gdps_prediction_model_run, ]

    monkeypatch.setattr(app.db.database, 'get_write_session',
                        mock_get_session_gdps)
    monkeypatch.setattr(app.models.env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_gdps_prediction_model_run_timestamp_records)

    def mock_get_session_hrdps(*args):

        return UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'HRDPS',
                                  PredictionModel.projection == '2.5km')],
                [hrdps_prediction_model],
            ),
            (
                [mock.call.query(ProcessedModelRunUrl),
                 mock.call.filter(ProcessedModelRunUrl == hrdps_url)],
                [hrdps_processed_model_run]
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [hrdps_prediction_model_run]
            ),
            (
                [mock.call.query(PredictionModelGridSubset)],
                [PredictionModelGridSubset(
                    id=2, prediction_model_id=hrdps_prediction_model.id, geom=from_shape(shape))]
            )
        ])

    def mock_get_hrdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [hrdps_prediction_model_run, ]

    monkeypatch.setattr(app.db.database, 'get_write_session',
                        mock_get_session_hrdps)
    monkeypatch.setattr(app.models.env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_hrdps_prediction_model_run_timestamp_records)


@ pytest.fixture()
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

    def mock_requests_get_hrdps(*args, **kwargs):
        """ mock env_canada download method for HRDPS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_hrdps_continental_RH_TGL_2_ps2.5km_2020100700_P007-00.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_hrdps)


@ pytest.fixture()
def mock_download_fail(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        return MockResponse(status_code=400)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


def test_get_gdps_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    total_num_of_urls = 81 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(list(env_canada.get_global_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


def test_get_hrdps_download_urls():
    """ test to see if get_download_urls methods gives the correct number of urls """
    total_num_of_urls = 49 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(list(env_canada.get_high_res_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


def test_main_gdps(mock_download, mock_session, mock_utcnow, mock_get_processed_file_count):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "GDPS"]
    assert env_canada.main() == 1


# def test_main_hrdps(mock_download, mock_session, mock_utcnow, mock_get_processed_file_count):
#     """ run main method to see if it runs successfully. """
#     # All files, except one, are marked as already having been downloaded, so we expect one file to
#     # be processed.
#     sys.argv = ["argv", "HRDPS"]
#     assert env_canada.main() == 1


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

# pylint: enable=unused-argument, redefined-outer-name
