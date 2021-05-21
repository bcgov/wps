""" Unit testing for hourly actuals bot (Marvin) """
from app.time_utils import get_utc_now
import asyncio
import os
import logging
import pytest
from pytest_mock import MockerFixture
from app.fireweather_bot import hourly_actuals
from app.schemas.observations import WeatherReading, WeatherStationHourlyReadings
from app.schemas.stations import WeatherStation
import nest_asyncio
nest_asyncio.apply()


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_hourly_actuals(mocker: MockerFixture):
    """ Mocks out hourly actuals as async result """
    reading_1 = WeatherReading(datetime=get_utc_now())
    reading_2 = WeatherReading(datetime=get_utc_now())
    station_1 = WeatherStation(code=1, name="one", lat=0, long=0)
    station_2 = WeatherStation(code=1, name="one", lat=0, long=0)
    readings_1 = WeatherStationHourlyReadings(values=[reading_1, reading_2], station=station_1)
    readings_2 = WeatherStationHourlyReadings(values=[reading_1, reading_2], station=station_2)

    future_hourly = asyncio.Future()
    future_hourly.set_result([readings_1, readings_2])
    mocker.patch('app.wildfire_one.get_hourly_readings', return_value=future_hourly)


@pytest.mark.asyncio
async def test_hourly_actuals_bot(mocker: MockerFixture, mock_requests_session, mock_hourly_actuals):  # pylint: disable=unused-argument
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    save_hourly_actuals_spy = mocker.spy(hourly_actuals, 'save_hourly_actual')
    with pytest.raises(SystemExit) as excinfo:
        await hourly_actuals.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There are 2 records for 2 stations in the fixture above so we expect 4 save calls.
    assert save_hourly_actuals_spy.call_count == 4


@pytest.mark.asyncio
async def test_hourly_actuals_bot_fail(mocker: MockerFixture,
                                       monkeypatch,
                                       mock_requests_session):  # pylint: disable=unused-argument
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    def mock_process_csv(self, filename: str):
        raise Exception()

    monkeypatch.setattr(hourly_actuals.HourlyActualsBot, 'process_csv', mock_process_csv)
    rocket_chat_spy = mocker.spy(hourly_actuals, 'send_rocketchat_notification')

    with pytest.raises(SystemExit) as excinfo:
        await hourly_actuals.main()
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

    hourly_actual = hourly_actuals.parse_hourly_actual(1, weather_reading)
    assert hourly_actual.rh_valid is True
    assert hourly_actual.temp_valid is True
    assert hourly_actual.wdir_valid is True
    assert hourly_actual.precip_valid is True
    assert hourly_actual.wspeed_valid is True
