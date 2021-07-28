""" Unit testing for hourly actuals bot (Marvin) """
import asyncio
import math
import os
import logging
import pytest
from pytest_mock import MockerFixture
from app.db.models.observations import HourlyActual
from app.utils.time import get_utc_now
from app.fireweather_bot import hourly_actuals
from app.schemas.observations import WeatherReading
from app.wildfire_one.wfwx_api import WFWXWeatherStation
from app.wildfire_one import wfwx_api


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_hourly_actuals(mocker: MockerFixture):
    """ Mocks out hourly actuals as async result """
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
            hourlyMeasurementTypeCode=MockWFWXHourlyResponse(
                id="ACTUAL",
                displayLabel="Actual",
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

    wfwx_hourly_1 = build_mock_wfwx_response('1')
    wfwx_hourly_2 = build_mock_wfwx_response('2')

    future_station_codes = asyncio.Future()
    future_station_codes.set_result([station_1, station_2])

    mocker.patch('app.wildfire_one.wfwx_api.wfwx_station_list_mapper', return_value=future_station_codes)
    mocker.patch('app.wildfire_one.wfwx_api.get_hourly_actuals_all_stations',
                 return_value=[wfwx_hourly_1, wfwx_hourly_2])
    mocker.patch('app.wildfire_one.wildfire_fetchers.fetch_paged_response_generator',
                 return_value=iter([wfwx_hourly_1, wfwx_hourly_2]))


def test_hourly_actuals_bot(monkeypatch, mocker: MockerFixture, mock_requests_session, mock_hourly_actuals):  # pylint: disable=unused-argument
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """

    @asyncio.coroutine
    def mock_get_auth_header(_):
        return dict()

    monkeypatch.setattr(wfwx_api, 'get_auth_header', mock_get_auth_header)
    save_hourly_actuals_spy = mocker.spy(hourly_actuals, 'save_hourly_actual')
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There 1 records for 2 stations in the fixture above so we expect 2 save calls.
    assert save_hourly_actuals_spy.call_count == 2


def test_hourly_actuals_bot_fail(mocker: MockerFixture,
                                 monkeypatch,
                                 mock_requests_session):  # pylint: disable=unused-argument
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    def mock_get_hourly_readings(self, filename: str):
        raise Exception()

    monkeypatch.setattr(wfwx_api, 'get_hourly_readings', mock_get_hourly_readings)
    rocket_chat_spy = mocker.spy(hourly_actuals, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_parse_hourly_actual():
    """ Valid fields are set when values exist """
    weather_reading = WeatherReading(
        datetime=get_utc_now(),
        temperature=0.0,
        relative_humidity=0.0,
        wind_speed=0.0,
        wind_direction=0.0,
        barometric_pressure=0.0,
        precipitation=0.0,
        dewpoint=0.0,
        ffmc=0.0,
        isi=0.0,
        fwi=0.0
    )

    hourly_actual = wfwx_api.parse_hourly_actual(1, weather_reading)
    assert hourly_actual.rh_valid is True
    assert hourly_actual.temp_valid is True
    assert hourly_actual.wdir_valid is True
    assert hourly_actual.precip_valid is True
    assert hourly_actual.wspeed_valid is True


def test_invalid_metrics():
    """ Metric valid flags should be false """
    weather_reading = WeatherReading(
        datetime=get_utc_now(),
        temperature=0.0,
        relative_humidity=101,
        wind_speed=-1,
        wind_direction=361,
        barometric_pressure=0.0,
        precipitation=-1,
        dewpoint=0.0,
        ffmc=0.0,
        isi=0.0,
        fwi=0.0)

    hourly_actual = wfwx_api.parse_hourly_actual(1, weather_reading)
    assert isinstance(hourly_actual, HourlyActual)
    assert hourly_actual.temp_valid is True
    assert hourly_actual.precip_valid is False
    assert hourly_actual.wspeed_valid is False
    assert hourly_actual.wdir_valid is False


def test_invalid_metrics_from_wfwx():
    """ Metric valid flags should be false """
    weather_reading = WeatherReading(
        datetime=get_utc_now(),
        temperature=1,
        relative_humidity=1,
        wind_speed=1,
        wind_direction=1,
        barometric_pressure=0.0,
        precipitation=None,
        dewpoint=0.0,
        ffmc=0.0,
        isi=0.0,
        fwi=0.0,
        observation_valid=False,
        observation_valid_comment="Precipitation can not be null."
    )

    hourly_actual = wfwx_api.parse_hourly_actual(1, weather_reading)
    assert isinstance(hourly_actual, HourlyActual)
    assert hourly_actual.temp_valid is True
    assert hourly_actual.precip_valid is False
    assert hourly_actual.precipitation is math.nan
