from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponseError
from app.morecast_v2 import forecasts
from wps_shared.schemas.morecast_v2 import MoreCastForecastInput
from wps_shared.schemas.stations import WFWXWeatherStation
from wps_wf1.wfwx_api import WfwxApi

TIMESTAMP = 1720123200000
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


def http_error(status):
    return ClientResponseError(Mock(real_url="https://wf1/test"), (), status=status)


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
        {"station_code": 1, "station_name": "station1", "for_date": TIMESTAMP}
    ]
    api.post_forecasts.assert_awaited_once_with(forecasts=result.forecasts)
    api.get_dailies_generator.assert_awaited_once_with(
        wfwx_stations=STATIONS,
        time_of_interest=datetime.fromtimestamp(TIMESTAMP / 1000, timezone.utc),
        end_time_of_interest=datetime.fromtimestamp(TIMESTAMP / 1000, timezone.utc),
        check_cache=False,
        use_no_cache_header=True,
    )
    assert api.get_wfwx_stations_from_station_codes.call_args.kwargs == {
        "use_no_cache_header": True
    }


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
        dailies([daily(2, "ACTUAL")]),
    ]
    api.post_forecasts.side_effect = http_error(400)
    result = await forecasts.publish_wf1_forecasts(api, ROWS, "user")

    assert result.forecasts == []
    assert [row.station_code for row in result.skipped] == [1, 2]
    assert result.station_ids == ["1", "2"]
    api.post_forecasts.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize("status", [400, 401, 500])
async def test_unrelated_post_error_is_not_retried(api, status):
    api.get_dailies_generator.side_effect = [dailies([]), dailies([])]
    error = http_error(status)
    api.post_forecasts.side_effect = error
    with pytest.raises(ClientResponseError) as raised:
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")
    assert raised.value is error
    api.post_forecasts.assert_awaited_once()
    assert api.get_dailies_generator.await_count == (2 if status == 400 else 1)


@pytest.mark.anyio
async def test_retry_failure_stops_after_second_post(api):
    api.get_dailies_generator.side_effect = [dailies([]), dailies([daily(1, "ACTUAL")])]
    api.post_forecasts.side_effect = http_error(400)
    with pytest.raises(ClientResponseError):
        await forecasts.publish_wf1_forecasts(api, ROWS, "user")
    assert api.post_forecasts.await_count == 2
    assert api.get_dailies_generator.await_count == 2


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
