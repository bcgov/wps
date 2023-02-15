""" Unit tests for the fireweather noon forecats job """
import os
import logging
import pytest
from pytest_mock import MockerFixture
from app.jobs import noon_forecasts
from app.tests.jobs.job_fixtures import mock_wfwx_stations, mock_wfwx_response
from app.wildfire_one import wfwx_api

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_noon_forecasts(mocker: MockerFixture):
    """ Mocks out noon forecasts as async result """
    wfwx_hourlies = mock_wfwx_response()
    future_wfwx_stations = mock_wfwx_stations()

    mocker.patch('app.wildfire_one.wfwx_api.wfwx_station_list_mapper', return_value=future_wfwx_stations)
    mocker.patch('app.wildfire_one.wfwx_api.get_noon_forecasts_all_stations',
                 return_value=wfwx_hourlies)
    mocker.patch('app.wildfire_one.wildfire_fetchers.fetch_paged_response_generator',
                 return_value=iter(wfwx_hourlies))


def test_noon_forecasts_bot(monkeypatch, mocker: MockerFixture, mock_noon_forecasts):  # pylint: disable=unused-argument
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    async def mock_get_auth_header(_):
        return dict()

    monkeypatch.setattr(wfwx_api, 'get_auth_header', mock_get_auth_header)
    save_noon_forecast_spy = mocker.spy(noon_forecasts, 'save_noon_forecast')
    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There 1 records for 2 stations in the fixture above so we expect 2 save calls.
    assert save_noon_forecast_spy.call_count == 2


def test_noon_forecasts_bot_fail(mocker: MockerFixture,
                                 monkeypatch):  # pylint: disable=unused-argument
    """
    Test that when the bot fails a message is sent to
    rocket-chat, and our exit code is 1.
    """

    def mock_get_noon_forecasts():
        raise Exception()

    monkeypatch.setattr(wfwx_api, 'get_noon_forecasts_all_stations', mock_get_noon_forecasts)
    rocket_chat_spy = mocker.spy(noon_forecasts, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
