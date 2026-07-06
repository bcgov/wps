"""Unit tests for the RDPS SFMS downloader job."""

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import requests
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from wps_shared.weather_models import CompletedWithSomeExceptions

from app.jobs import rdps_sfms

MODULE_PATH = "app.jobs.rdps_sfms"
RDPS_URL = (
    "https://dd.weather.gc.ca/today/model_rdps/10km/00/001/"
    "20260623T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT001H.grib2"
)
JOB_NOW = datetime(2026, 6, 23, 8, tzinfo=timezone.utc)


class FakeRDPSGrib:
    files_downloaded = 0

    def __init__(self, exception_count: int, connection_error_count: int):
        self.exception_count = exception_count
        self.connection_error_count = connection_error_count

    async def process(self):
        return None

    async def apply_retention_policy(self, days_to_retain: int):
        return None


@contextmanager
def write_session_scope():
    yield MagicMock(spec=Session)


def patch_job_dependencies(mocker: MockerFixture, fake_rdps_grib: FakeRDPSGrib):
    mocker.patch(f"{MODULE_PATH}.time_utils.get_utc_now", return_value=JOB_NOW)
    mocker.patch(f"{MODULE_PATH}.get_write_session_scope", write_session_scope)
    mocker.patch(f"{MODULE_PATH}.RDPSGrib", return_value=fake_rdps_grib)
    mocker.patch(f"{MODULE_PATH}.compute_and_store_precip_rasters", AsyncMock())


@pytest.mark.parametrize(
    ("download_error", "expected_connection_errors", "expected_exceptions"),
    [
        (requests.ConnectionError("HPFX and DD both unreachable"), 1, 0),
        (requests.Timeout("request timed out"), 1, 0),
        (requests.HTTPError("503 Server Error"), 0, 1),
    ],
)
@pytest.mark.anyio
async def test_process_model_run_urls_classifies_download_errors(
    mocker: MockerFixture,
    download_error: Exception,
    expected_connection_errors: int,
    expected_exceptions: int,
):
    mocker.patch(f"{MODULE_PATH}.get_saved_model_run_for_sfms", return_value=None)
    fetcher = MagicMock()
    fetcher.get.side_effect = download_error

    rdps_grib = rdps_sfms.RDPSGrib(MagicMock(spec=Session))

    await rdps_grib._process_model_run_urls(0, "temp", [RDPS_URL], fetcher)

    assert rdps_grib.connection_error_count == expected_connection_errors
    assert rdps_grib.exception_count == expected_exceptions


@pytest.mark.anyio
async def test_rdps_job_does_not_fail_for_connection_errors_only(mocker: MockerFixture):
    patch_job_dependencies(mocker, FakeRDPSGrib(exception_count=0, connection_error_count=2))

    await rdps_sfms.RDPSJob().run()


@pytest.mark.anyio
async def test_rdps_job_fails_for_unexpected_exceptions(mocker: MockerFixture):
    patch_job_dependencies(mocker, FakeRDPSGrib(exception_count=1, connection_error_count=0))

    with pytest.raises(CompletedWithSomeExceptions):
        await rdps_sfms.RDPSJob().run()
