"""Unit testing for hourly actuals job"""

import os
from datetime import UTC, datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.sfms import SFMSDaily
from wps_weather_data.by_time import ACTUALS, DAILY, HOURLY, ByTimeTable
from wps_weather_data.stations import StationsTable
from wps_weather_data.wf1 import Wf1Table

from app.jobs import hourly_actuals

AT_1900 = datetime(2026, 11, 17, 19, tzinfo=UTC)
AT_2000 = datetime(2026, 11, 17, 20, tzinfo=UTC)


def hourly_actual(station_code: int, temperature: float, time: datetime = AT_1900) -> HourlyActual:
    # wps_wf1 gives the time as an ISO string.
    return HourlyActual(
        station_code=station_code,
        weather_date=time.isoformat(),
        temperature=temperature,
        relative_humidity=60.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=0.2,
    )


@pytest.fixture
def tables(monkeypatch, tmp_path):
    wf1 = Wf1Table(str(tmp_path / "wf1"))
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    monkeypatch.setattr(hourly_actuals, "Wf1Table", lambda: wf1)
    monkeypatch.setattr(hourly_actuals, "ByTimeTable", lambda: by_time)
    stations = StationsTable(str(tmp_path / "stations"))
    monkeypatch.setattr(hourly_actuals, "StationsTable", lambda: stations)
    return wf1, by_time, stations


def test_hourly_actuals_job_writes_wf1_and_by_time(mocker: MockerFixture, mock_wfwx_api, tables):
    wf1, by_time, _ = tables
    mock_wfwx_api.get_hourly_actuals_all_stations.return_value = [
        hourly_actual(1, 10.0),
        hourly_actual(2, 11.0),
    ]
    mocker.patch("app.jobs.hourly_actuals.WfwxApi", return_value=mock_wfwx_api)

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()

    assert excinfo.value.code == 0
    assert wf1.dataset().count_rows() == 2
    rows = by_time.read(HOURLY, [ACTUALS], AT_1900, AT_1900).to_pylist()
    assert [(row["station_code"], row["temperature"]) for row in rows] == [(1, 10.0), (2, 11.0)]
    assert rows[0]["precipitation"] == pytest.approx(0.2)


def test_hourly_actuals_job_writes_wf1s_daily_actuals(mocker: MockerFixture, mock_wfwx_api, tables):
    wf1, by_time, _ = tables
    mocker.patch.object(
        hourly_actuals.wps_shared.utils.time,
        "get_pst_now",
        return_value=AT_2000 + timedelta(minutes=30),
    )
    mock_wfwx_api.get_hourly_actuals_all_stations.return_value = [hourly_actual(1, 10.0, AT_2000)]

    def dailies(time):
        if time != AT_2000:
            return []
        values = {"lat": 50.0, "lon": -120.0, "temperature": 10.0, "relative_humidity": 60.0}
        return [
            SFMSDaily(
                code=1, for_datetime=time, run_type=RunTypeEnum.actual, precipitation=7.4, **values
            ),
            # A forecast for the same time is not an actual.
            SFMSDaily(
                code=2,
                for_datetime=time,
                run_type=RunTypeEnum.forecast,
                precipitation=1.0,
                **values,
            ),
        ]

    mock_wfwx_api.get_sfms_daily_weather_all_stations.side_effect = dailies
    mocker.patch("app.jobs.hourly_actuals.WfwxApi", return_value=mock_wfwx_api)

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()

    assert excinfo.value.code == 0
    # The latest 20:00 UTC and the one before are both asked for.
    asked = [
        call.args[0] for call in mock_wfwx_api.get_sfms_daily_weather_all_stations.call_args_list
    ]
    assert asked == [AT_2000 - timedelta(days=1), AT_2000]
    (row,) = by_time.read(DAILY, [ACTUALS], AT_2000, AT_2000).to_pylist()
    assert (row["station_code"], row["temperature"]) == (1, 10.0)
    # WF1's total, not the sum of the hours fetched.
    assert row["precipitation"] == pytest.approx(7.4)
    # One hourly row and one daily row, both as WF1 supplied them.
    assert wf1.dataset().count_rows() == 2


def test_hourly_actuals_job_records_only_changes_in_wf1(
    mocker: MockerFixture, mock_wfwx_api, tables
):
    wf1, by_time, _ = tables
    mocker.patch("app.jobs.hourly_actuals.WfwxApi", return_value=mock_wfwx_api)
    for fetched in ([hourly_actual(1, 10.0)], [hourly_actual(1, 10.0)], [hourly_actual(1, 12.0)]):
        mock_wfwx_api.get_hourly_actuals_all_stations.return_value = fetched
        with pytest.raises(SystemExit):
            hourly_actuals.main()

    # The second fetch was the same; the third was a correction.
    assert sorted(wf1.dataset().to_table()["temperature"].to_pylist()) == [10.0, 12.0]
    rows = by_time.read(HOURLY, [ACTUALS], AT_1900, AT_1900).to_pylist()
    assert [row["temperature"] for row in rows] == [12.0]


def test_hourly_actuals_job_fail(mocker: MockerFixture, mock_wfwx_api, tables):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    mock_wfwx_api.get_hourly_actuals_all_stations = mocker.AsyncMock(side_effect=Exception())
    mocker.patch("app.jobs.hourly_actuals.WfwxApi", return_value=mock_wfwx_api)
    chatops_spy = mocker.spy(hourly_actuals, "send_chatops_notification")

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert chatops_spy.call_count == 1


def test_hourly_actuals_job_writes_wf1s_stations(mocker: MockerFixture, mock_wfwx_api, tables):
    _, _, stations = tables
    mock_wfwx_api.get_hourly_actuals_all_stations.return_value = []
    mock_wfwx_api.get_station_data.return_value = [
        {"stationCode": 322, "displayLabel": "AFTON", "stationStatus": {"id": "ACTIVE"}}
    ]
    mocker.patch("app.jobs.hourly_actuals.WfwxApi", return_value=mock_wfwx_api)

    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()

    assert excinfo.value.code == 0
    rows = stations.read().to_pylist()
    assert [(row["station_code"], row["name"], row["status"]) for row in rows] == [
        (322, "AFTON", "ACTIVE")
    ]


@pytest.mark.anyio
async def test_raw_stations_keeps_wf1s_records():
    async def pages():
        yield {"stationCode": 1}
        yield {"stationCode": 2}

    assert await hourly_actuals._raw_stations(pages()) == [{"stationCode": 1}, {"stationCode": 2}]
