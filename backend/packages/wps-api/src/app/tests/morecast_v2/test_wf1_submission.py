from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponseError
from app.morecast_v2 import forecasts
from wps_shared.schemas.morecast_v2 import MoreCastForecastInput
from wps_shared.schemas.stations import WFWXWeatherStation
from wps_wf1.wfwx_api import WfwxApi

TIMESTAMP = 1720123200000
STATION_FOREIGN_KEY_ERROR = (
    "ORA-02291: integrity constraint (APP_WF1_WEATHER.DWXM_WS_FK) violated - parent key not found"
)
ROWS = [
    MoreCastForecastInput(
        station_code=code, for_date=TIMESTAMP, temp=20, rh=40, precip=0, wind_speed=10
    )
    for code in (1, 2)
]
STATIONS = [
    WFWXWeatherStation(
        wfwx_id=str(code),
        code=code,
        name=f"station{code}",
        latitude=50,
        longitude=-120,
        elevation=100,
        zone_code="1",
    )
    for code in (1, 2)
]


def daily(code, record_type, timestamp=TIMESTAMP, forecast_id="existing"):
    return {
        "id": forecast_id,
        "createdBy": "original",
        "stationData": {
            "stationCode": code,
            "stationStatus": {"id": "ACTIVE"},
            "latitude": 50,
            "longitude": -120,
        },
        "weatherTimestamp": timestamp,
        "recordType": {"id": record_type},
    }


async def dailies(rows):
    for row in rows:
        yield row


def http_error(status, message=""):
    return ClientResponseError(
        Mock(real_url="https://wf1/test"), (), status=status, message=message
    )


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(forecasts, "get_fire_centre_station_codes", lambda: [])
    result = AsyncMock(spec=WfwxApi)
    result.get_wfwx_stations_from_station_codes.return_value = STATIONS
    return result


@pytest.mark.anyio
@pytest.mark.parametrize("observed_type", ["ACTUAL", "MANUAL"])
async def test_skip_observed_and_preserve_existing_forecast(api, observed_type):
    api.get_dailies_generator.return_value = dailies(
        [daily(1, "FORECAST"), daily(1, observed_type), daily(2, "FORECAST")]
    )
    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert [row.stationId for row in result.forecasts] == ["2"]
    assert result.forecasts[0].id == "existing"
    assert result.forecasts[0].createdBy == "original"
    assert [row.model_dump() for row in result.skipped] == [
        {
            "station_code": 1,
            "station_name": "station1",
            "for_date": TIMESTAMP,
            "reason": "actual_exists",
        }
    ]
    api.post_forecasts.assert_awaited_once_with(forecasts=result.forecasts)
    api.get_dailies_generator.assert_awaited_once_with(
        wfwx_stations=STATIONS,
        time_of_interest=datetime.fromtimestamp(TIMESTAMP / 1000, timezone.utc),
        end_time_of_interest=datetime.fromtimestamp(TIMESTAMP / 1000, timezone.utc),
        check_cache=False,
        use_no_cache_header=True,
    )
    assert api.get_wfwx_stations_from_station_codes.call_args.kwargs == {"use_cache": False}


@pytest.mark.anyio
async def test_match_exact_station_and_timestamp(api):
    next_day = ROWS[0].model_copy(update={"for_date": TIMESTAMP + 86400000})
    api.get_dailies_generator.return_value = dailies(
        [daily(1, "ACTUAL"), daily(3, "ACTUAL"), daily(2, "ACTUAL", TIMESTAMP - 86400000)]
    )
    result = await forecasts.publish_wf1_forecasts(api, [*ROWS, next_day], "user")

    assert [(row.stationId, row.weatherTimestamp) for row in result.forecasts] == [
        ("2", TIMESTAMP),
        ("1", next_day.for_date),
    ]
    assert all(row.id is None and row.createdBy == "user" for row in result.forecasts)


@pytest.mark.anyio
async def test_all_skipped_avoids_post(api):
    api.get_dailies_generator.return_value = dailies([daily(1, "ACTUAL"), daily(2, "MANUAL")])
    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert result.forecasts == []
    assert len(result.skipped) == 2
    assert result.station_ids == ["1", "2"]
    api.post_forecasts.assert_not_awaited()


@pytest.mark.anyio
async def test_unavailable_station_does_not_block_other_forecasts(api):
    unavailable = ROWS[0].model_copy(update={"station_code": 3})
    api.get_dailies_generator.return_value = dailies([daily(1, "ACTUAL"), daily(2, "FORECAST")])

    result = await forecasts.publish_wf1_forecasts(api, [*ROWS, unavailable], "user")

    assert [row.stationId for row in result.forecasts] == ["2"]
    assert [(row.station_code, row.reason, row.station_name) for row in result.skipped] == [
        (1, "actual_exists", "station1"),
        (3, "station_unavailable", None),
    ]
    assert all(row.for_date == TIMESTAMP for row in result.skipped)
    api.post_forecasts.assert_awaited_once_with(forecasts=result.forecasts)


@pytest.mark.anyio
async def test_all_unavailable_avoids_daily_lookup_and_post(api):
    api.get_wfwx_stations_from_station_codes.return_value = []

    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert result.forecasts == []
    assert result.station_ids == []
    assert [row.station_code for row in result.skipped] == [1, 2]
    assert all(
        row.reason == "station_unavailable" and row.station_name is None for row in result.skipped
    )
    api.get_dailies_generator.assert_not_awaited()
    api.post_forecasts.assert_not_awaited()


@pytest.mark.anyio
async def test_station_lookup_failure_does_not_become_skipped(api):
    error = http_error(503)
    api.get_wfwx_stations_from_station_codes.side_effect = error

    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert raised.value is error
    api.get_dailies_generator.assert_not_awaited()
    api.post_forecasts.assert_not_awaited()


@pytest.mark.anyio
async def test_empty_submission_avoids_wf1(api):
    result = await forecasts.publish_wf1_forecasts(api, [], "user")
    assert result.forecasts == result.skipped == result.station_ids == []
    api.get_wfwx_stations_from_station_codes.assert_not_awaited()
    api.get_dailies_generator.assert_not_awaited()
    api.post_forecasts.assert_not_awaited()


@pytest.mark.anyio
async def test_retry_excludes_new_actuals_and_refreshes_forecast_ids(api):
    api.get_dailies_generator.side_effect = [
        dailies([]),
        dailies([daily(1, "ACTUAL"), daily(2, "FORECAST", forecast_id="fresh")]),
    ]
    api.post_forecasts.side_effect = [http_error(400), None]

    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert api.post_forecasts.await_count == 2
    first, second = api.post_forecasts.await_args_list
    assert len(first.kwargs["forecasts"]) == 2
    assert second.kwargs["forecasts"] == result.forecasts
    assert result.forecasts[0].id == "fresh"
    assert result.forecasts[0].createdBy == "original"
    assert [row.station_code for row in result.skipped] == [1]


@pytest.mark.anyio
async def test_retry_retains_initial_skips_and_avoids_empty_post(api):
    api.get_dailies_generator.side_effect = [
        dailies([daily(1, "ACTUAL")]),
        dailies([daily(1, "ACTUAL"), daily(2, "ACTUAL")]),
    ]
    api.post_forecasts.side_effect = http_error(400)
    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert result.forecasts == []
    assert [row.station_code for row in result.skipped] == [1, 2]
    assert result.station_ids == ["1", "2"]
    api.post_forecasts.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status, message", [(400, STATION_FOREIGN_KEY_ERROR), (401, ""), (500, "")]
)
async def test_unrelated_post_error_is_not_retried(api, status, message):
    api.get_dailies_generator.side_effect = [dailies([]), dailies([])]
    error = http_error(status, message)
    api.post_forecasts.side_effect = error
    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")
    assert raised.value is error
    api.post_forecasts.assert_awaited_once()
    assert api.get_dailies_generator.await_count == (2 if status == 400 else 1)


@pytest.mark.anyio
@pytest.mark.parametrize("max_retries", [pytest.param(None, id="default"), 0, 1, 2])
async def test_retry_limit_stops_without_an_extra_lookup(api, max_retries):
    retry_limit = 1 if max_retries is None else max_retries
    retry_options = {} if max_retries is None else {"max_retries": max_retries}
    rows = [ROWS[0].model_copy(update={"for_date": TIMESTAMP + day * 86400000}) for day in range(4)]
    api.get_dailies_generator.side_effect = [
        dailies([daily(1, "ACTUAL", timestamp=row.for_date) for row in rows[:attempt]])
        for attempt in range(retry_limit + 1)
    ]
    errors = [http_error(400) for _ in range(retry_limit + 1)]
    api.post_forecasts.side_effect = errors

    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, rows, "user", **retry_options)

    assert raised.value is errors[-1]
    assert api.post_forecasts.await_count == retry_limit + 1
    assert api.get_dailies_generator.await_count == retry_limit + 1


@pytest.mark.anyio
async def test_multiple_retries_preserve_skips_and_refresh_forecast_ids(api):
    next_day = TIMESTAMP + 86400000
    last_day = TIMESTAMP + 2 * 86400000
    rows = [
        *ROWS,
        ROWS[1].model_copy(update={"for_date": next_day}),
        ROWS[1].model_copy(update={"for_date": last_day}),
    ]
    api.get_wfwx_stations_from_station_codes.side_effect = lambda codes, *_args, **_kwargs: [
        station for station in STATIONS if station.code in codes
    ]
    api.get_dailies_generator.side_effect = [
        dailies([daily(1, "ACTUAL")]),
        dailies(
            [daily(1, "ACTUAL"), daily(2, "ACTUAL"), daily(2, "FORECAST", next_day, "interim")]
        ),
        dailies(
            [
                daily(1, "ACTUAL"),
                daily(2, "ACTUAL"),
                daily(2, "MANUAL", next_day),
                daily(2, "FORECAST", last_day, "fresh"),
            ]
        ),
    ]
    api.post_forecasts.side_effect = [http_error(400), http_error(400), None]

    result = await forecasts.publish_wf1_forecasts(api, rows, "user", max_retries=2)

    assert api.post_forecasts.await_count == 3
    first, second, third = api.post_forecasts.await_args_list
    assert [len(call.kwargs["forecasts"]) for call in (first, second, third)] == [3, 2, 1]
    assert second.kwargs["forecasts"][0].id == "interim"
    assert third.kwargs["forecasts"] == result.forecasts
    assert result.forecasts[0].id == "fresh"
    assert result.forecasts[0].createdBy == "original"
    assert result.forecasts[0].weatherTimestamp == last_day
    assert [(row.station_code, row.for_date) for row in result.skipped] == [
        (1, TIMESTAMP),
        (2, TIMESTAMP),
        (2, next_day),
    ]
    assert result.station_ids == ["1", "2"]
    assert api.get_wfwx_stations_from_station_codes.await_count == 3
    assert all(
        set(call.args[0]) == {1, 2}
        for call in api.get_wfwx_stations_from_station_codes.await_args_list
    )


@pytest.mark.anyio
async def test_multiple_retries_stop_when_all_rows_become_observed(api):
    api.get_dailies_generator.side_effect = [
        dailies([]),
        dailies([daily(1, "ACTUAL")]),
        dailies([daily(1, "ACTUAL"), daily(2, "MANUAL")]),
    ]
    api.post_forecasts.side_effect = http_error(400)

    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user", max_retries=2)

    assert result.forecasts == []
    assert [row.station_code for row in result.skipped] == [1, 2]
    assert api.post_forecasts.await_count == 2
    assert api.get_dailies_generator.await_count == 3


@pytest.mark.anyio
async def test_retry_uses_latest_snapshot_when_skipped_keys_change(api):
    api.get_dailies_generator.side_effect = [
        dailies([daily(1, "ACTUAL")]),
        dailies([daily(1, "FORECAST", forecast_id="refreshed"), daily(2, "MANUAL")]),
    ]
    api.post_forecasts.side_effect = [http_error(400), None]

    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    first, second = api.post_forecasts.await_args_list
    assert [row.stationId for row in first.kwargs["forecasts"]] == ["2"]
    assert second.kwargs["forecasts"] == result.forecasts
    assert [row.stationId for row in result.forecasts] == ["1"]
    assert result.forecasts[0].id == "refreshed"
    assert result.forecasts[0].createdBy == "original"
    assert [row.station_code for row in result.skipped] == [2]
    assert result.station_ids == ["1", "2"]


@pytest.mark.anyio
async def test_retry_requires_new_skips_even_when_retries_remain(api):
    api.get_dailies_generator.side_effect = [
        dailies([daily(1, "ACTUAL")]),
        dailies([daily(1, "ACTUAL")]),
    ]
    error = http_error(400)
    api.post_forecasts.side_effect = error

    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, ROWS, "user", max_retries=3)

    assert raised.value is error
    api.post_forecasts.assert_awaited_once()
    assert api.get_dailies_generator.await_count == 2


@pytest.mark.anyio
async def test_actual_on_previously_unavailable_station_does_not_trigger_retry(api):
    api.get_wfwx_stations_from_station_codes.side_effect = [STATIONS[1:], STATIONS]
    api.get_dailies_generator.side_effect = [dailies([]), dailies([daily(1, "ACTUAL")])]
    error = http_error(400)
    api.post_forecasts.side_effect = error

    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert raised.value is error
    api.post_forecasts.assert_awaited_once()
    assert [row.stationId for row in api.post_forecasts.await_args.kwargs["forecasts"]] == ["2"]
    assert api.get_dailies_generator.await_count == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "remaining, unavailable_codes",
    [(STATIONS[1:], [1]), ([], [1, 2])],
    ids=["partial", "all_unavailable"],
)
async def test_retry_excludes_stations_that_become_unavailable(api, remaining, unavailable_codes):
    api.get_wfwx_stations_from_station_codes.side_effect = [STATIONS, remaining]
    api.get_dailies_generator.side_effect = [dailies([]), dailies([])]
    api.post_forecasts.side_effect = [http_error(400, STATION_FOREIGN_KEY_ERROR), None]

    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert [row.stationId for row in result.forecasts] == [station.wfwx_id for station in remaining]
    assert [row.station_code for row in result.skipped] == unavailable_codes
    assert all(row.reason == "station_unavailable" for row in result.skipped)
    assert result.station_ids == [station.wfwx_id for station in remaining]
    assert api.post_forecasts.await_count == 1 + bool(remaining)
    assert api.get_wfwx_stations_from_station_codes.await_count == 2
    assert api.get_dailies_generator.await_count == 1 + bool(remaining)
    if remaining:
        assert api.post_forecasts.await_args.kwargs["forecasts"] == result.forecasts


@pytest.mark.anyio
@pytest.mark.parametrize("retry", [False, True])
async def test_lookup_failure_stops_publication(api, retry):
    api.get_dailies_generator.side_effect = (
        [dailies([]), http_error(503)] if retry else http_error(503)
    )
    api.post_forecasts.side_effect = http_error(400)
    with pytest.raises(ClientResponseError):
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")
    assert api.post_forecasts.await_count == int(retry)
