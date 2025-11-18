"""Unit tests for app/env_canada.py"""

import os
import sys
import logging
from typing import Optional
import pytest
import requests
import datetime
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from wps_shared.weather_models.job_utils import (
    HRDPS_GRIB_LAYERS,
    get_high_res_model_run_download_urls,
)
import wps_shared.utils.time as time_utils
import wps_shared.db.database
import wps_shared.db.crud.weather_models
import wps_jobs.weather_model_jobs.env_canada
import wps_jobs.weather_model_jobs.common_model_fetchers
import wps_jobs.weather_model_jobs.utils.process_grib
from wps_shared.weather_models import ProjectionEnum
from wps_shared.db.models.weather_models import (
    PredictionModel,
    ProcessedModelRunUrl,
    PredictionModelRunTimestamp,
)
from wps_shared.tests.common import default_mock_client_get
from tests.weather_models.test_env_canada_gdps import MockResponse


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_database(monkeypatch):
    """Mocked out database queries"""
    hrdps_url = (
        "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/"
        "00/001/20200521T00Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT001H.grib2"
    )
    hrdps_processed_model_run = ProcessedModelRunUrl(url=hrdps_url)
    hrdps_prediction_model = PredictionModel(
        id=3,
        abbreviation="HRDPS",
        projection="ps2.5km",
        name="High Resolution Deterministic Prediction System",
    )
    hrdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1,
        prediction_model_id=hrdps_prediction_model.id,
        prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=hrdps_prediction_model,
        complete=True,
    )

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        return hrdps_prediction_model

    def mock_get_hrdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(hrdps_prediction_model_run, hrdps_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != hrdps_url:
            return hrdps_processed_model_run
        return None

    def mock_get_prediction_run(*args, **kwargs):
        return hrdps_prediction_model_run

    monkeypatch.setattr(
        wps_jobs.weather_model_jobs.utils.process_grib,
        "get_prediction_model",
        mock_get_prediction_model,
    )
    monkeypatch.setattr(
        wps_jobs.weather_model_jobs.common_model_fetchers,
        "get_prediction_model_run_timestamp_records",
        mock_get_hrdps_prediction_model_run_timestamp_records,
    )
    monkeypatch.setattr(
        wps_jobs.weather_model_jobs.env_canada,
        "get_processed_file_record",
        mock_get_processed_file_record,
    )
    monkeypatch.setattr(
        wps_shared.db.crud.weather_models, "get_prediction_run", mock_get_prediction_run
    )


@pytest.fixture()
def mock_get_processed_file_record(monkeypatch):
    """Mock "get_processed_file_record" to only return the None on the 1st call."""
    called = False

    def get_processed_file_record(session: Session, url: str):
        nonlocal called
        if called:
            return ProcessedModelRunUrl()
        called = True
        return None

    monkeypatch.setattr(
        wps_jobs.weather_model_jobs.env_canada,
        "get_processed_file_record",
        get_processed_file_record,
    )


@pytest.fixture()
def mock_download(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get_hrdps(*args, **kwargs):
        """mock env_canada download method for HRDPS"""
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, "20230317T18Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT001H.grib2"
        )
        with open(filename, "rb") as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)

    monkeypatch.setattr(requests, "get", mock_requests_get_hrdps)


def test_get_hrdps_download_urls():
    """test to see if get_download_urls methods gives the correct number of urls"""
    # -1 because 000 hour has no APCP_SFC_0
    total_num_of_urls = 49 * len(HRDPS_GRIB_LAYERS) - 1
    assert (
        len(list(get_high_res_model_run_download_urls(time_utils.get_utc_now(), 0)))
        == total_num_of_urls
    )


@pytest.mark.usefixtures("mock_get_processed_file_record")
def test_process_hrdps(mock_download, mock_database, monkeypatch: pytest.MonkeyPatch):
    """run process method to see if it runs successfully."""
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "HRDPS"]
    assert wps_jobs.weather_model_jobs.env_canada.process_models() == 1


def test_main_fail(mocker: MockerFixture, monkeypatch):
    """Run the main method, check that message is sent to rocket chat, and exit code is EX_SOFTWARE"""
    sys.argv = ["argv", "HRDPS"]

    def mock_process_models():
        raise Exception()

    rocket_chat_spy = mocker.spy(
        wps_jobs.weather_model_jobs.env_canada, "send_rocketchat_notification"
    )
    monkeypatch.setattr(
        wps_jobs.weather_model_jobs.env_canada, "process_models", mock_process_models
    )

    with pytest.raises(SystemExit) as excinfo:
        wps_jobs.weather_model_jobs.env_canada.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_parse_high_res_model_url_correct_format():
    """Given a grib file download URL in the correct format, env_canada.parse_high_res_model_url
    should return the correct info pulled from the URL"""
    test_cases = [
        {
            "url": "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/06/012/20230322T06Z_MSC_HRDPS_TMP_AGL-2m_RLatLon0.0225_PT012.grib2",
            "variable_name": "TMP_AGL-2m",
            "projection": ProjectionEnum.HIGH_RES_CONTINENTAL,
            "model_run_timestamp": datetime.datetime(
                2023, 3, 22, 6, 0, tzinfo=datetime.timezone.utc
            ),
            "prediction_timestamp": datetime.datetime(
                2023, 3, 22, 18, 0, tzinfo=datetime.timezone.utc
            ),
        },
        {
            "url": "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/06/012/20230322T06Z_MSC_HRDPS_WIND_AGL-10m_RLatLon0.0225_PT012.grib2",
            "variable_name": "WIND_AGL-10m",
            "projection": ProjectionEnum.HIGH_RES_CONTINENTAL,
            "model_run_timestamp": datetime.datetime(
                2023, 3, 22, 6, 0, tzinfo=datetime.timezone.utc
            ),
            "prediction_timestamp": datetime.datetime(
                2023, 3, 22, 18, 0, tzinfo=datetime.timezone.utc
            ),
        },
        {
            "url": "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/06/012/20230322T06Z_MSC_HRDPS_APCP_Sfc_RLatLon0.0225_PT012.grib2",
            "variable_name": "APCP_Sfc",
            "projection": ProjectionEnum.HIGH_RES_CONTINENTAL,
            "model_run_timestamp": datetime.datetime(
                2023, 3, 22, 6, 0, tzinfo=datetime.timezone.utc
            ),
            "prediction_timestamp": datetime.datetime(
                2023, 3, 22, 18, 0, tzinfo=datetime.timezone.utc
            ),
        },
        {
            "url": "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/12/084/20230322T12Z_MSC_HRDPS_RH_AGL-2m_RLatLon0.0225_PT084.grib2",
            "variable_name": "RH_AGL-2m",
            "projection": ProjectionEnum.HIGH_RES_CONTINENTAL,
            "model_run_timestamp": datetime.datetime(
                2023, 3, 22, 12, 0, tzinfo=datetime.timezone.utc
            ),
            "prediction_timestamp": datetime.datetime(
                2023, 3, 26, 0, 0, tzinfo=datetime.timezone.utc
            ),
        },
    ]

    for case in test_cases:
        (
            actual_variable_name,
            actual_projection,
            actual_model_run_timestamp,
            actual_prediction_timestamp,
        ) = wps_jobs.weather_model_jobs.env_canada.parse_high_res_model_url(case["url"])
        assert actual_variable_name == case["variable_name"]
        assert actual_projection == case["projection"]
        assert actual_model_run_timestamp == case["model_run_timestamp"]
        assert actual_prediction_timestamp == case["prediction_timestamp"]


def test_part_high_res_model_url_incorrect_format():
    """Tests basic functionality to detect issues in HRDPS URL formats - Exceptions should be raised
    because given URLs are missing vital pieces of info"""
    bad_urls = [
        "https://dd.weather.gc.ca/bad_format",
        "https://dd.weather.gc.ca/model_hrdps/moo",
        "https://dd.weather.gc.ca/model_hrdps/continental/25km/",
        "https://dd.weather.gc.ca/model_hrps/wrong_model_name",
        "https://dd.weather.gc.ca/model_hrdps/continental/2.5km/00/MSC_ASDF_ASDFASDF.grib2",
    ]

    for test_case in bad_urls:
        with pytest.raises(Exception):
            wps_jobs.weather_model_jobs.env_canada.parse_high_res_model_url(test_case)
