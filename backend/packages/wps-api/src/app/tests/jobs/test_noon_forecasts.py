"""Unit tests for the fireweather noon forecasts job"""

import os
from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.forecasts import NoonForecast
from wps_weather_data.by_time import DAILY, FORECAST, ByTimeTable
from wps_weather_data.wf1 import Wf1Table

from app.jobs import noon_forecasts

NOON = datetime(2026, 11, 18, 20, tzinfo=UTC)


def noon_forecast(station_code: int, temperature: float) -> NoonForecast:
    # wps_wf1 gives the time as an ISO string.
    return NoonForecast(
        station_code=station_code,
        weather_date=NOON.isoformat(),
        temperature=temperature,
        relative_humidity=40.0,
        wind_speed=10.0,
        wind_direction=270.0,
        precipitation=1.5,
    )


@pytest.fixture
def tables(monkeypatch, tmp_path):
    wf1 = Wf1Table(str(tmp_path / "wf1"))
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    monkeypatch.setattr(noon_forecasts, "Wf1Table", lambda: wf1)
    monkeypatch.setattr(noon_forecasts, "ByTimeTable", lambda: by_time)
    return wf1, by_time


def test_noon_forecasts_bot_writes_wf1_and_by_time(mocker: MockerFixture, mock_wfwx_api, tables):
    wf1, by_time = tables
    mocker.patch("app.jobs.noon_forecasts.WfwxApi", return_value=mock_wfwx_api)
    mock_wfwx_api.get_noon_forecasts_all_stations.return_value = [
        noon_forecast(1, 15.0),
        noon_forecast(2, 16.0),
    ]

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()

    assert excinfo.value.code == 0
    assert wf1.dataset().count_rows() == 2
    rows = by_time.read(DAILY, [FORECAST], NOON, NOON).to_pylist()
    assert [(row["station_code"], row["temperature"]) for row in rows] == [(1, 15.0), (2, 16.0)]
    assert rows[0]["precipitation"] == pytest.approx(1.5)


def test_noon_forecasts_bot_keeps_each_changed_forecast(
    mocker: MockerFixture, mock_wfwx_api, tables
):
    wf1, by_time = tables
    mocker.patch("app.jobs.noon_forecasts.WfwxApi", return_value=mock_wfwx_api)
    for fetched in ([noon_forecast(1, 15.0)], [noon_forecast(1, 15.0)], [noon_forecast(1, 13.0)]):
        mock_wfwx_api.get_noon_forecasts_all_stations.return_value = fetched
        with pytest.raises(SystemExit):
            noon_forecasts.main()

    # wf1 keeps the forecast's history; by_time has the latest.
    assert sorted(wf1.dataset().to_table()["temperature"].to_pylist()) == [13.0, 15.0]
    rows = by_time.read(DAILY, [FORECAST], NOON, NOON).to_pylist()
    assert [row["temperature"] for row in rows] == [13.0]


def test_noon_forecasts_bot_fail(mocker: MockerFixture, mock_wfwx_api, tables):
    """
    Test that when the bot fails a message is sent to
    rocket-chat, and our exit code is 1.
    """

    mock_wfwx_api.get_noon_forecasts_all_stations = mocker.AsyncMock(side_effect=Exception())
    mocker.patch("app.jobs.noon_forecasts.WfwxApi", return_value=mock_wfwx_api)
    chatops_spy = mocker.spy(noon_forecasts, "send_chatops_notification")

    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert chatops_spy.call_count == 1
