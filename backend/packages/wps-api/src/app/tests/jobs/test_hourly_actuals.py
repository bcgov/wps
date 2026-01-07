"""Unit testing for hourly actuals job"""

import logging
import os
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from app.jobs import hourly_actuals
from app.tests.jobs.job_fixtures import mock_wfwx_response, mock_wfwx_stations

logger = logging.getLogger(__name__)


def test_hourly_actuals_job(mocker: MockerFixture, mock_wfwx_api):
    """Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """

    wfwx_hourlies = mock_wfwx_response()
    mock_wfwx_api.get_hourly_actuals_all_stations.return_value = wfwx_hourlies
    mocker.patch("app.jobs.hourly_actuals.create_wfwx_api", return_value=mock_wfwx_api)

    save_hourly_actuals_spy = mocker.spy(hourly_actuals, "save_hourly_actual")
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There 1 records for 2 stations in the fixture above so we expect 2 save calls.
    assert save_hourly_actuals_spy.call_count == 2


def test_hourly_actuals_job_fail(mocker: MockerFixture, mock_wfwx_api):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    mock_wfwx_api.get_hourly_actuals_all_stations = mocker.AsyncMock(side_effect=Exception())
    mocker.patch("app.jobs.hourly_actuals.create_wfwx_api", return_value=mock_wfwx_api)
    rocket_chat_spy = mocker.spy(hourly_actuals, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
