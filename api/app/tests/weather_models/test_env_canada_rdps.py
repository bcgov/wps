""" Unit tests for app/env_canada.py """

import os
import sys
from contextlib import contextmanager
import logging
import pytest
import requests
import shapely.wkt
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
# TODO: Get rid of UnifiedAlchemyMagicMock
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.utils.time as time_utils
import app.db.database
from app.weather_models import env_canada
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           PredictionModelGridSubset)
# pylint: disable=unused-import
from app.tests.weather_models.test_env_canada_gdps import (MockResponse, mock_get_stations,
                                                           mock_get_model_run_predictions_for_grid,
                                                           mock_get_actuals_left_outer_join_with_predictions)
# pylint: disable=unused-argument, redefined-outer-name


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session object """
    geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
            " -120.525 50.62500000000001, -120.525 50.77500000000001))")
    shape = shapely.wkt.loads(geom)

    rdps_url = ('https://dd.weather.gc.ca/model_gem_regional/10km/grib2/00/034/'
                'CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2')
    rdps_processed_model_run = ProcessedModelRunUrl(url=rdps_url)
    rdps_prediction_model = PredictionModel(id=2,
                                            abbreviation='RDPS',
                                            projection='ps10km',
                                            name='Regional Deterministic Prediction System')
    rdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=2, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=rdps_prediction_model, complete=True)

    @contextmanager
    def mock_get_session_rdps_scope(*args):

        yield UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'RDPS',
                                  PredictionModel.projection == 'ps10km')],
                [rdps_prediction_model],
            ),
            (
                [mock.call.query(ProcessedModelRunUrl),
                 mock.call.filter(ProcessedModelRunUrl.url == rdps_url)],
                [rdps_processed_model_run]
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [rdps_prediction_model_run]
            ),
            (
                [mock.call.query(PredictionModelGridSubset)],
                [PredictionModelGridSubset(
                    id=1, prediction_model_id=rdps_prediction_model.id, geom=from_shape(shape))]
            )
        ])

    def mock_get_rdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(rdps_prediction_model_run, rdps_prediction_model)]

    monkeypatch.setattr(app.db.database, 'get_write_session_scope',
                        mock_get_session_rdps_scope)
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
                      mock_session,
                      mock_get_model_run_predictions_for_grid,
                      mock_get_actuals_left_outer_join_with_predictions,
                      mock_get_stations):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "RDPS"]
    assert env_canada.process_models() == 1

# pylint: enable=unused-argument, redefined-outer-name
# pylint: enable=unused-import
