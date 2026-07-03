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


@pytest.mark.anyio
async def test_process_model_run_urls_tracks_connection_errors_separately(mocker: MockerFixture):
    mocker.patch(f"{MODULE_PATH}.get_saved_model_run_for_sfms", return_value=None)
    fetcher = MagicMock()
    fetcher.get.side_effect = requests.ConnectionError("HPFX and DD both unreachable")

    rdps_grib = rdps_sfms.RDPSGrib(MagicMock(spec=Session))

    await rdps_grib._process_model_run_urls(0, "temp", [RDPS_URL], fetcher)

    assert rdps_grib.connection_error_count == 1
    assert rdps_grib.exception_count == 0


@pytest.mark.anyio
async def test_process_model_run_urls_tracks_http_errors_as_exceptions(mocker: MockerFixture):
    mocker.patch(f"{MODULE_PATH}.get_saved_model_run_for_sfms", return_value=None)
    fetcher = MagicMock()
    fetcher.get.side_effect = requests.HTTPError("503 Server Error")

    rdps_grib = rdps_sfms.RDPSGrib(MagicMock(spec=Session))

    await rdps_grib._process_model_run_urls(0, "temp", [RDPS_URL], fetcher)

    assert rdps_grib.connection_error_count == 0
    assert rdps_grib.exception_count == 1


@pytest.mark.anyio
async def test_rdps_job_does_not_fail_for_connection_errors_only(mocker: MockerFixture):
    class FakeRDPSGrib:
        files_downloaded = 0
        exception_count = 0
        connection_error_count = 2

        async def process(self):
            return None

        async def apply_retention_policy(self, days_to_retain: int):
            return None

    @contextmanager
    def write_session_scope():
        yield MagicMock(spec=Session)

    fake_rdps_grib = FakeRDPSGrib()
    mocker.patch(
        f"{MODULE_PATH}.time_utils.get_utc_now",
        return_value=datetime(2026, 6, 23, 8, tzinfo=timezone.utc),
    )
    mocker.patch(f"{MODULE_PATH}.get_write_session_scope", write_session_scope)
    mocker.patch(f"{MODULE_PATH}.RDPSGrib", return_value=fake_rdps_grib)
    mocker.patch(f"{MODULE_PATH}.compute_and_store_precip_rasters", AsyncMock())

    await rdps_sfms.RDPSJob().run()


@pytest.mark.anyio
async def test_rdps_job_fails_for_unexpected_exceptions(mocker: MockerFixture):
    class FakeRDPSGrib:
        files_downloaded = 0
        exception_count = 1
        connection_error_count = 0

        async def process(self):
            return None

        async def apply_retention_policy(self, days_to_retain: int):
            return None

    @contextmanager
    def write_session_scope():
        yield MagicMock(spec=Session)

    fake_rdps_grib = FakeRDPSGrib()
    mocker.patch(
        f"{MODULE_PATH}.time_utils.get_utc_now",
        return_value=datetime(2026, 6, 23, 8, tzinfo=timezone.utc),
    )
    mocker.patch(f"{MODULE_PATH}.get_write_session_scope", write_session_scope)
    mocker.patch(f"{MODULE_PATH}.RDPSGrib", return_value=fake_rdps_grib)
    mocker.patch(f"{MODULE_PATH}.compute_and_store_precip_rasters", AsyncMock())

    with pytest.raises(CompletedWithSomeExceptions):
        await rdps_sfms.RDPSJob().run()
