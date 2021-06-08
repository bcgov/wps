""" Unit tests for the fireweather noon forecats bot (Bender) """
import os
import logging
import datetime
import pytest
from pytest_mock import MockerFixture
from app.fireweather_bot import noon_forecasts
import app.utils.time

logger = logging.getLogger(__name__)


def test_noon_forecasts_bot(mocker: MockerFixture, mock_requests_session):  # pylint: disable=unused-argument
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    save_noon_forecast_spy = mocker.spy(noon_forecasts, 'save_noon_forecast')
    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There are 352 records in the csv fixture, one of which doesn't have a valid station name,
    # so we expect 351 records.
    assert save_noon_forecast_spy.call_count == 351


def test_noon_forecasts_bot_fail_in_season(mocker: MockerFixture,
                                           monkeypatch,
                                           mock_requests_session):  # pylint: disable=unused-argument
    """
    Test that when the bot fails and the current date is within fire season, a message is sent to
    rocket-chat, and our exit code is 1.
    """

    def mock_process_csv(self, filename: str):
        raise Exception()

    def mock_get_utc_now():
        return datetime.datetime(2020, 7, 1)

    monkeypatch.setattr(noon_forecasts.NoonForecastBot, 'process_csv', mock_process_csv)
    monkeypatch.setattr(app.utils.time, 'get_utc_now', mock_get_utc_now)
    rocket_chat_spy = mocker.spy(noon_forecasts, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_noon_forecasts_bot_fail_outside_season(mocker: MockerFixture,
                                                monkeypatch,
                                                mock_requests_session):  # pylint: disable=unused-argument
    """
    Test that when the bot fails and the current date is outside fire season, no RC message is sent.
    Assert exit code 1.
    """

    def mock_process_csv(self, filename: str):
        raise Exception()

    def mock_get_utc_now():
        return datetime.datetime(2020, 12, 31)

    monkeypatch.setattr(noon_forecasts.NoonForecastBot, 'process_csv', mock_process_csv)
    monkeypatch.setattr(app.utils.time, 'get_utc_now', mock_get_utc_now)
    rocket_chat_spy = mocker.spy(noon_forecasts, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was NOT called
    assert rocket_chat_spy.call_count == 0
