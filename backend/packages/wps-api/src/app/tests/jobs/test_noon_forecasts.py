"""Unit tests for the fireweather noon forecats job"""

import logging
import os

import pytest
from pytest_mock import MockerFixture

from app.jobs import noon_forecasts
from app.tests.jobs.job_fixtures import mock_wfwx_response

logger = logging.getLogger(__name__)


def test_noon_forecasts_bot(monkeypatch, mocker: MockerFixture, mock_wfwx_api):
    """Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """

    wfwx_hourlies = mock_wfwx_response()
    mock_wfwx_api.get_noon_forecasts_all_stations.return_value = wfwx_hourlies
    mocker.patch("app.jobs.noon_forecasts.WfwxApi", return_value=mock_wfwx_api)
    save_noon_forecast_spy = mocker.spy(noon_forecasts, "save_noon_forecast")
    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There 1 records for 2 stations in the fixture above so we expect 2 save calls.
    assert save_noon_forecast_spy.call_count == 2


def test_noon_forecasts_bot_fail(mocker: MockerFixture, monkeypatch, mock_wfwx_api):
    """
    Test that when the bot fails a message is sent to
    rocket-chat, and our exit code is 1.
    """

    mock_wfwx_api.get_noon_forecasts_all_stations = mocker.AsyncMock(side_effect=Exception())
    rocket_chat_spy = mocker.spy(noon_forecasts, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
