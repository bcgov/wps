""" Unit testing for CWFIS grass curing data processing """

import os
import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from app.jobs import grass_curing
from app.jobs.grass_curing import GrassCuringJob


def test_grass_curing_job_fail(mocker: MockerFixture,
                                 monkeypatch):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    async def mock__run_grass_curing(self):
        raise OSError("Error")

    monkeypatch.setattr(GrassCuringJob, '_run_grass_curing', mock__run_grass_curing)
    rocket_chat_spy = mocker.spy(grass_curing, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_grass_curing_job_exits_without_error_when_no_work_required(monkeypatch):
    """ Test that grass_curing_job exits without error when no data needs to be processed.
    """
    async def mock__get_last_for_date(self):
        return datetime.now()
    
    monkeypatch.setattr(GrassCuringJob, '_get_last_for_date', mock__get_last_for_date)

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK
    