""" Unit testing for hourly actuals job """
import math
import os
import logging
import pytest
from pytest_mock import MockerFixture
from app.db.models.observations import HourlyActual
from app.tests.jobs.job_fixtures import mock_wfwx_stations, mock_wfwx_response
from app.utils.time import get_utc_now
from app.jobs import hourly_actuals
from app.wildfire_one import wfwx_api


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_hourly_actuals(mocker: MockerFixture):
    """ Mocks out hourly actuals as async result """
    wfwx_hourlies = mock_wfwx_response()
    future_wfwx_stations = mock_wfwx_stations()
    mocker.patch('app.wildfire_one.wfwx_api.wfwx_station_list_mapper', return_value=future_wfwx_stations)
    mocker.patch('app.wildfire_one.wfwx_api.get_hourly_actuals_all_stations',
                 return_value=wfwx_hourlies)
    mocker.patch('app.wildfire_one.wildfire_fetchers.fetch_paged_response_generator',
                 return_value=iter(wfwx_hourlies))


def test_hourly_actuals_job(monkeypatch, mocker: MockerFixture, mock_hourly_actuals):
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """

    async def mock_get_auth_header(_):
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


def test_hourly_actuals_job_fail(mocker: MockerFixture,
                                 monkeypatch,
                                 mock_requests_session):
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
    raw_actual = {
        "weatherTimestamp": get_utc_now().timestamp(),
        "temperature": 0.0,
        "relativeHumidity": 0.0,
        "windSpeed": 0.0,
        "windDirection": 0.0,
        "precipitation": 0.0,
        "fineFuelMoistureCode": 0.0,
        "initialSpreadIndex": 0.0,
        "fireWeatherIndex": 0.0
    }

    hourly_actual = wfwx_api.parse_hourly_actual(1, raw_actual)
    assert isinstance(hourly_actual, HourlyActual)
    assert hourly_actual.rh_valid is True
    assert hourly_actual.temp_valid is True
    assert hourly_actual.wdir_valid is True
    assert hourly_actual.precip_valid is True
    assert hourly_actual.wspeed_valid is True


def test_invalid_metrics():
    """ Metric valid flags should be false """

    raw_actual = {
        "weatherTimestamp": get_utc_now().timestamp(),
        "temperature": 0.0,
        "relativeHumidity": 101,
        "windSpeed": -1,
        "windDirection": 361,
        "precipitation": -1,
        "fineFuelMoistureCode": 0.0,
        "initialSpreadIndex": 0.0,
        "fireWeatherIndex": 0.0
    }

    hourly_actual = wfwx_api.parse_hourly_actual(1, raw_actual)
    assert isinstance(hourly_actual, HourlyActual)
    assert hourly_actual.temp_valid is True
    assert hourly_actual.rh_valid is False
    assert hourly_actual.precip_valid is False
    assert hourly_actual.wspeed_valid is False
    assert hourly_actual.wdir_valid is False


def test_invalid_metrics_from_wfwx():
    """ Metric valid flags should be false """

    raw_actual = {
        "weatherTimestamp": get_utc_now().timestamp(),
        "temperature": 0.0,
        "relativeHumidity": 101,
        "windSpeed": -1,
        "windDirection": 361,
        "fineFuelMoistureCode": 0.0,
        "initialSpreadIndex": 0.0,
        "fireWeatherIndex": 0.0,
        "observationValid": False,
        "observationValidComment": "Precipitation can not be null."
    }

    hourly_actual = wfwx_api.parse_hourly_actual(1, raw_actual)
    assert isinstance(hourly_actual, HourlyActual)
    assert hourly_actual.temp_valid is True
    assert hourly_actual.rh_valid is False
    assert hourly_actual.precip_valid is False
    assert hourly_actual.wspeed_valid is False
    assert hourly_actual.wdir_valid is False
    assert hourly_actual.precipitation is math.nan
