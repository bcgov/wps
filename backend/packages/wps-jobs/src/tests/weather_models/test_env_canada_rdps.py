"""Unit tests for app/env_canada.py"""

import logging
import os
import sys

import pytest
import requests
import weather_model_jobs.env_canada
import wps_shared.utils.time as time_utils
from aiohttp import ClientSession
from tests.weather_models.test_env_canada_gdps import (  # noqa: F401 (fixture)
    MockResponse,
    only_first_url_unprocessed,
)
from wps_shared.tests.common import default_mock_client_get
from wps_shared.weather_models.model_run_urls import (
    RDPS_GRIB_LAYERS,
    get_regional_model_run_download_urls,
)

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_download(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get_rdps(*args, **kwargs):
        """mock env_canada download method for RDPS"""
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, "20260602T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT000H.grib2"
        )
        with open(filename, "rb") as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)

    monkeypatch.setattr(requests.Session, "get", mock_requests_get_rdps)


@pytest.fixture()
def mock_download_fail(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get(*args, **kwargs):
        """mock env_canada download method"""
        return MockResponse(status_code=400)

    monkeypatch.setattr(requests, "get", mock_requests_get)


def test_get_rdps_download_urls():
    """test to see if get_download_urls methods give the correct number of urls"""
    # -1 because 000 hour has no APCP_Sfc
    total_num_of_urls = 85 * len(RDPS_GRIB_LAYERS) - 1
    assert (
        len(list(get_regional_model_run_download_urls(time_utils.get_utc_now(), 0)))
        == total_num_of_urls
    )


@pytest.mark.usefixtures("only_first_url_unprocessed")
def test_process_rdps(mock_download, monkeypatch: pytest.MonkeyPatch):
    """run main method to see if it runs successfully."""
    # All files, except one, are treated as already processed, so we expect one file to be
    # processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "RDPS"]
    assert weather_model_jobs.env_canada.process_models() == 1
