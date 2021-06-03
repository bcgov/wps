""" Very basic test for worker - essential just testing if it runs without exceptions """
import os
from datetime import datetime
import pytest
import requests
from app import configure_logging
from app.weather_models import ModelEnum, ProjectionEnum
from app.db.database import Session
from app.db.models.weather_models import PredictionModel
from app.db.models.c_haines import CHainesModelRun
import app.db.crud.c_haines
import app.c_haines.severity_index
from app.c_haines.worker import main
from app.tests.common import MockResponse

configure_logging()


@pytest.fixture()
def mock_get_prediction_model(monkeypatch):
    """ fixture for crud """
    # pylint: disable=unused-argument
    def _mock_get_prediction_model(session: Session,
                                   abbreviation: ModelEnum,
                                   projection: ProjectionEnum) -> PredictionModel:
        return PredictionModel(abbreviation='GDPS')

    monkeypatch.setattr(app.c_haines.severity_index, 'get_prediction_model', _mock_get_prediction_model)


@pytest.fixture()
def mock_get_c_haines_model_run(monkeypatch):
    """ fixture for crud """

    # pylint: disable=unused-argument
    def _mock_get_c_haines_model_run(session: Session,
                                     model_run_timestamp: datetime,
                                     prediction_model: PredictionModel):
        return CHainesModelRun(id=1, model_run_timestamp=datetime.now(), prediction_model_id=1,
                               prediction_model=PredictionModel(abbreviation='GDPS'))
    monkeypatch.setattr(app.db.crud.c_haines, 'get_c_haines_model_run', _mock_get_c_haines_model_run)


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    # pylint: disable=unused-argument
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        print('mock download {}'.format(args[0]))
        dirname = os.path.dirname(os.path.realpath(__file__))
        if 'TMP_ISBL' in args[0]:
            if '700' in args[0]:
                grib_filename = 'CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021012618_P048-00.grib2'
            if '850' in args[0]:
                grib_filename = 'CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021012618_P048-00.grib2'
        elif 'DEPR_ISBL' in args[0]:
            grib_filename = 'CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2'
        filename = os.path.join(dirname, grib_filename)
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


@pytest.mark.usefixtures('mock_download', 'mock_get_c_haines_model_run', 'mock_get_prediction_model',
                         'mock_get_minio_client')
def test_c_haines_worker():
    """ Test the c-haines worked.
    This is not a very focused test. Through the magic of sqlalchmy, it will only
    process one set of grib files. We check that the main process runs ok without raising
    any exceptions.
    """
    try:
        main()
    except Exception as exception:  # pylint: disable=broad-except
        pytest.fail(exception)
