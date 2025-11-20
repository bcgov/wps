""" Unit testing for VIIRS snow data processing """

import os
import pytest
from datetime import date, datetime, timedelta
from pytest_mock import MockerFixture
from requests import Response
from requests.exceptions import HTTPError
from app.jobs import viirs_snow
from app.jobs.viirs_snow import ViirsSnowJob


async def mock__get_bc_boundary_from_s3(self, temp_dir):
    return


def test_viirs_snow_job_fail(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    async def mock__get_last_processed_date(self):
        raise OSError("Error")

    monkeypatch.setattr(ViirsSnowJob, '_get_last_processed_date', mock__get_last_processed_date)
    rocket_chat_spy = mocker.spy(viirs_snow, 'send_rocketchat_notification')
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_viirs_snow_job_exits_without_error_when_no_work_required(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    """ Test that viirs_snow_job exits without error when no data needs to be processed.
    """

    async def mock__get_last_processed_date(self, for_date: datetime):
        return date.today() - timedelta(days=1)
    
    monkeypatch.setattr(ViirsSnowJob, '_get_last_processed_date', mock__get_last_processed_date)
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK
    

def test_viirs_snow_job_exits_cleanly_when_no_viirs_data(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    """ Test that viirs_snow_job exits cleanly when attempt to download data that doesn't exist
    throws a HTTPError with status code of 501.
    """

    async def mock__get_last_processed_date(self, for_date: datetime):
        return date.today() - timedelta(days=2)
    

    def mock__download_viirs_granules_by_date(self, for_date: date, path: str, file_name: str):
        error = HTTPError(response=Response())
        error.response.status_code = 501
        raise error

    monkeypatch.setattr(ViirsSnowJob, '_get_last_processed_date', mock__get_last_processed_date)
    monkeypatch.setattr(ViirsSnowJob, '_get_bc_boundary_from_s3', mock__get_bc_boundary_from_s3)
    monkeypatch.setattr(ViirsSnowJob, '_download_viirs_granules_by_date', mock__download_viirs_granules_by_date)
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK


def test_viirs_snow_job_fails_on_nsidc_auth_failure(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    """
    Test that when authentication with the NSIDC fails a message is sent to rocket-chat and our exit code is 1.
    """

    async def mock__get_last_processed_date(self):
        return date.today() - timedelta(days=2)

    def mock__download_viirs_granules_by_date(self, for_date: date, path: str, file_name: str):
        error = HTTPError(response=Response())
        error.response.status_code = 401
        raise error

    monkeypatch.setattr(ViirsSnowJob, '_get_last_processed_date', mock__get_last_processed_date)   
    monkeypatch.setattr(ViirsSnowJob, '_get_bc_boundary_from_s3', mock__get_bc_boundary_from_s3)
    monkeypatch.setattr(ViirsSnowJob, '_download_viirs_granules_by_date', mock__download_viirs_granules_by_date)
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    rocket_chat_spy = mocker.spy(viirs_snow, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1