""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import pytest
import requests
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.time_utils as time_utils
import app.db.database
from app.models import env_canada
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           PredictionModelGridSubset)
from app.tests.models.test_env_canada_gdps import MockResponse
# pylint: disable=unused-argument, redefined-outer-name


logger = logging.getLogger(__name__)


@ pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session object """
    geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
            " -120.525 50.62500000000001, -120.525 50.77500000000001))")
    shape = shapely.wkt.loads(geom)

    hrdps_url = 'https://dd.weather.gc.ca/model_hrdps/continental/grib2/00/007/' \
        + 'CMC_hrdps_continental_TMP_TGL_2_ps2.5km_2020100700_P007-00.grib2'
    hrdps_processed_model_run = ProcessedModelRunUrl(url=hrdps_url)
    hrdps_prediction_model = PredictionModel(id=3, abbreviation='HRDPS', projection='ps2.5km',
                                             name='High Resolution Deterministic Prediction System')
    hrdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=3, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=hrdps_prediction_model, complete=True)

    def mock_get_session_hrdps(*args):

        return UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'HRDPS',
                                  PredictionModel.projection == 'ps2.5km')],
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
                    id=1, prediction_model_id=hrdps_prediction_model.id, geom=from_shape(shape))]
            )
        ])

    def mock_get_hrdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(hrdps_prediction_model_run, hrdps_prediction_model)]

    monkeypatch.setattr(app.db.database, 'get_write_session',
                        mock_get_session_hrdps)
    monkeypatch.setattr(app.models.env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_hrdps_prediction_model_run_timestamp_records)


@ pytest.fixture()
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
    total_num_of_urls = 49 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(list(env_canada.get_high_res_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


def test_main_hrdps(mock_download, mock_session):
    """ run main method to see if it runs successfully. """
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    sys.argv = ["argv", "HRDPS"]
    assert env_canada.main() == 1


# pylint: enable=unused-argument, redefined-outer-name
