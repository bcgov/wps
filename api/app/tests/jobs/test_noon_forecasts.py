""" Unit tests for the fireweather noon forecats bot (Bender) """
import asyncio
import os
import logging
import datetime
import pytest
from pytest_mock import MockerFixture
from app.jobs import noon_forecasts
from app.wildfire_one.wfwx_api import WFWXWeatherStation
from app.wildfire_one import wfwx_api
import app.utils.time

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_noon_forecasts(mocker: MockerFixture):
    """ Mocks out noon forecasts as async result """
    station_1 = WFWXWeatherStation(latitude=1, longitude=1, elevation=1,
                                   wfwx_id='ba28973a-0a79-04ea-e053-1d09228e8c64', code=1,
                                   name='blah', zone_code='T1')
    station_2 = WFWXWeatherStation(latitude=1, longitude=1, elevation=1,
                                   wfwx_id='ba28973a-0a79-04ea-e053-1d09228e8c65', code=2,
                                   name='blah', zone_code='T1')

    class MockWFWXHourlyResponse(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def build_mock_wfwx_response(station_id: str) -> MockWFWXHourlyResponse:
        return MockWFWXHourlyResponse(
            stationId=station_id,
            id="ba289776-ef86-04ea-e053-1d09228e8c64",
            station="https://i1bcwsapi.nrs.gov.bc.ca/wfwx-fireweather-api/v1/stations/ba28973a-0a79-04ea-e053-1d09228e8c64",
            createdBy="LEGACY_DATA_LOAD",
            lastModifiedBy="LEGACY_DATA_LOAD",
            lastEntityUpdateTimestamp=1455788589000,
            updateDate="2021-01-31T01:10:34.000+0000",
            archive=False,
            weatherTimestamp=1455771600000,
            temperature=6.7,
            relativeHumidity=100.0,
            windSpeed=1.5,
            recordType=MockWFWXHourlyResponse(
                id="FORECAST",
                displayLabel="Forecast",
                displayOrder=1,
                createdBy="DATA_LOAD",
                lastModifiedBy="DATA_LOAD"
            ),
            windDirection=165.0,
            barometricPressure=None,
            precipitation=0.26,
            observationValidInd=True,
            observationValidComment=None,
            calculate=True,
            businessKey="1455771600000-ba28973a-0a79-04ea-e053-1d09228e8c64",
            fineFuelMoistureCode=5.603,
            initialSpreadIndex=0.0,
            fireWeatherIndex=0.0)

    wfwx_noon_forecast_1 = build_mock_wfwx_response('1')
    wfwx_noon_forecast_2 = build_mock_wfwx_response('2')

    future_station_codes = asyncio.Future()
    future_station_codes.set_result([station_1, station_2])

    mocker.patch('app.wildfire_one.wfwx_api.wfwx_station_list_mapper', return_value=future_station_codes)
    mocker.patch('app.wildfire_one.wfwx_api.get_noon_forecasts_all_stations',
                 return_value=[wfwx_noon_forecast_1, wfwx_noon_forecast_2])
    mocker.patch('app.wildfire_one.wildfire_fetchers.fetch_paged_response_generator',
                 return_value=iter([wfwx_noon_forecast_1, wfwx_noon_forecast_2]))


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


def test_noon_forecasts_bot_fail_in_season(mocker: MockerFixture,
                                           monkeypatch):  # pylint: disable=unused-argument
    """
    Test that when the bot fails and the current date is within fire season, a message is sent to
    rocket-chat, and our exit code is 1.
    """

    def mock_get_utc_now():
        return datetime.datetime(2020, 7, 1)

    def mock_get_noon_forecasts():
        raise Exception()

    monkeypatch.setattr(wfwx_api, 'get_noon_forecasts_all_stations', mock_get_noon_forecasts)
    monkeypatch.setattr(app.utils.time, 'get_utc_now', mock_get_utc_now)
    rocket_chat_spy = mocker.spy(noon_forecasts, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_noon_forecasts_bot_fail_outside_season(mocker: MockerFixture,
                                                monkeypatch):  # pylint: disable=unused-argument
    """
    Test that when the bot fails and the current date is outside fire season, no RC message is sent.
    Assert exit code 1.
    """
    def mock_get_utc_now():
        return datetime.datetime(2020, 12, 31)

    def mock_get_noon_forecasts():
        raise Exception()

    monkeypatch.setattr(wfwx_api, 'get_noon_forecasts_all_stations', mock_get_noon_forecasts)
    monkeypatch.setattr(app.utils.time, 'get_utc_now', mock_get_utc_now)
    rocket_chat_spy = mocker.spy(noon_forecasts, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was NOT called
    assert rocket_chat_spy.call_count == 0
