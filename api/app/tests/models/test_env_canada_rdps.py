""" Unit tests for app/env_canada.py """

import os
import sys
import logging
import datetime
from datetime import datetime
import pytest
import requests
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
from pytest_mock import MockerFixture
import app.time_utils as time_utils
import app.db.database
from app.schemas import WeatherStation, Season
from app.models import env_canada, machine_learning
from app.db.models import (PredictionModel, ProcessedModelRunUrl, PredictionModelRunTimestamp,
                           PredictionModelGridSubset, ModelRunGridSubsetPrediction)
from app.tests.models.crud import get_actuals_left_outer_join_with_predictions
from app.tests.models.test_env_canada_gdps import MockResponse, mock_get_stations
# pylint: disable=unused-argument, redefined-outer-name


logger = logging.getLogger(__name__)


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

    def mock_get_session_rdps(*args):

        return UnifiedAlchemyMagicMock(data=[
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

    monkeypatch.setattr(app.db.database, 'get_write_session',
                        mock_get_session_rdps)
    monkeypatch.setattr(env_canada, 'get_prediction_model_run_timestamp_records',
                        mock_get_rdps_prediction_model_run_timestamp_records)


@ pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get_gdps(*args, **kwargs):
        """ mock env_canada download method for RDPS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'CMC_reg_RH_TGL_2_ps10km_2020110500_P034.grib2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_gdps)


@ pytest.fixture()
def mock_download_fail(monkeypatch):
    """ fixture for env_canada.download """
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        return MockResponse(status_code=400)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


def test_get_rdps_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    total_num_of_urls = 85 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(list(env_canada.get_regional_model_run_download_urls(
        time_utils.get_utc_now(), 0))) == total_num_of_urls


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


def test_main_fail(mocker: MockerFixture, monkeypatch):
    """ Run the main method, check that message is sent to rocket chat, and exit code is EX_SOFTWARE """
    sys.argv = ["argv", "RDPS"]

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

# pylint: enable=unused-argument, redefined-outer-name
