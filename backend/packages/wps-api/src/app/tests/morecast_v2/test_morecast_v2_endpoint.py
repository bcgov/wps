from datetime import datetime
from unittest.mock import AsyncMock, Mock

import aiohttp
import app.routers.morecast_v2
import pytest
import sentry_sdk
from aiohttp import ClientSession
from app.morecast_v2 import forecasts as forecast_service
from app.morecast_v2.forecasts import WF1ForecastSubmission
from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.transport import Transport
from wps_shared.schemas.morecast_v2 import (
    MoreCastForecastInput,
    MoreCastForecastRequest,
    StationDailyFromWF1,
    WF1ForecastRecordType,
    WF1PostForecast,
    WF1SkippedForecast,
)
from wps_shared.schemas.shared import StationsRequest
from wps_shared.tests.common import default_mock_client_get

morecast_v2_post_url = "/api/morecast-v2/forecast"
morecast_v2_get_url = "/api/morecast-v2/forecasts/2023-03-15"
morecast_v2_post_by_date_range_url = "/api/morecast-v2/forecasts/2023-03-15/2023-03-19"
today = "2022-10-07"
morecast_v2_post_yesterday_dailies_url = f"/api/morecast-v2/yesterday-dailies/{today}"
morecast_v2_post_determinates_url = "/api/morecast-v2/determinates/2023-03-15/2023-03-19"


decode_fn = "jwt.decode"


@pytest.fixture(autouse=True)
def chatops(mocker):
    return mocker.patch("app.routers.morecast_v2.send_chatops_notification")


forecast = MoreCastForecastRequest(
    token="testToken",
    forecasts=[
        MoreCastForecastInput(
            station_code=1,
            for_date=1,
            temp=10.0,
            rh=40.1,
            precip=70.2,
            wind_speed=20.3,
            wind_direction=40,
        )
    ],
)

stations = StationsRequest(stations=[1, 2])


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture()
async def async_client():
    from app.main import app as test_app

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="https://test"
    ) as test_client:
        yield test_client


def test_get_forecast_unauthorized(client: TestClient):
    """forecast role required for retrieving forecasts"""
    response = client.get(morecast_v2_get_url)
    assert response.status_code == 401


def test_get_forecast_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """forecast role required for persisting a forecast"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(app.routers.morecast_v2, "get_user_forecasts_for_date", lambda *_: [])

    response = client.get(morecast_v2_get_url)
    assert response.status_code == 200


def test_post_forecast_unauthorized(client: TestClient):
    """forecast role required for persisting a forecast"""
    response = client.post(morecast_v2_post_url, json=[])
    assert response.status_code == 401


def submission(eligible, skipped):
    return WF1ForecastSubmission(
        forecasts=[
            WF1PostForecast(
                stationId=str(code),
                station=f"https://wf1/stations/{code}",
                weatherTimestamp=1,
                temperature=10,
                relativeHumidity=40,
                precipitation=0,
                windSpeed=10,
                recordType=WF1ForecastRecordType(),
            )
            for code in eligible
        ],
        skipped=[
            WF1SkippedForecast(station_code=code, station_name=f"station{code}", for_date=1)
            for code in skipped
        ],
        station_ids=["1", "2"],
    )


@pytest.fixture
def publishing(monkeypatch, mocker):
    monkeypatch.setattr(
        decode_fn, lambda *_args, **_kwargs: MockJWTDecodeWithRole("morecast2_write_forecast")
    )
    api = AsyncMock()
    mocker.patch("app.routers.morecast_v2.WfwxApi", return_value=api)
    prepare = mocker.patch.object(forecast_service, "format_as_wf1_post_forecasts")
    save = mocker.patch("app.routers.morecast_v2.save_all_forecasts")
    cache = mocker.patch("app.routers.morecast_v2.clear_cache_matching")
    return api, prepare, save, cache


def forecast_batch():
    return {
        "forecasts": [
            forecast.forecasts[0].model_copy(update={"station_code": code}).model_dump()
            for code in (1, 2)
        ]
    }


@pytest.mark.parametrize("eligible, skipped", [([1, 2], []), ([2], [1]), ([], [1, 2])])
def test_post_forecast_saves_full_batch(client, publishing, eligible, skipped, chatops, mocker):
    log_error = mocker.spy(app.routers.morecast_v2.logger, "error")
    api, prepare, save, cache = publishing
    prepared = submission(eligible, skipped)
    prepare.return_value = prepared

    response = client.post(morecast_v2_post_url, json=forecast_batch())

    assert response.status_code == 201
    assert response.json()["wf1_published_count"] == len(eligible)
    assert response.json()["wf1_skipped"] == [row.model_dump() for row in prepared.skipped]
    assert [row["station_code"] for row in response.json()["forecasts"]] == [1, 2]
    save.assert_called_once()
    saved = save.call_args.args[1]
    assert [row.station_code for row in saved] == [1, 2]
    assert all(row.temp == 10.0 and row.for_date.timestamp() * 1000 == 1 for row in saved)
    assert api.post_forecasts.await_count == int(bool(eligible))
    assert {call.args[0] for call in cache.call_args_list} == {"1", "2"}
    log_error.assert_not_called()
    chatops.assert_not_called()


@pytest.mark.parametrize("remaining", [[], [2]])
def test_post_forecast_race_saves_full_batch_once(client, publishing, remaining, chatops, mocker):
    log_error = mocker.spy(app.routers.morecast_v2.logger, "error")
    api, prepare, save, _cache = publishing
    skipped = [code for code in (1, 2) if code not in remaining]
    prepare.side_effect = [submission([1, 2], []), submission(remaining, skipped)]
    api.post_forecasts.side_effect = [
        aiohttp.ClientResponseError(Mock(real_url="https://wf1/test"), (), status=400),
        None,
    ]

    response = client.post(morecast_v2_post_url, json=forecast_batch())

    assert response.status_code == 201
    assert response.json()["wf1_published_count"] == len(remaining)
    assert response.json()["wf1_skipped"][0]["station_code"] == 1
    save.assert_called_once()
    assert len(save.call_args.args[1]) == 2
    assert api.post_forecasts.await_count == (2 if remaining else 1)
    log_error.assert_not_called()
    chatops.assert_not_called()


@pytest.mark.parametrize(
    "failure", ["lookup", "post", "unrelated400", "retry_lookup", "retry_post"]
)
def test_post_forecast_error_does_not_save(client, publishing, failure, chatops, mocker):
    log_error = mocker.spy(app.routers.morecast_v2.logger, "error")
    api, prepare, save, _cache = publishing
    error = aiohttp.ClientResponseError(Mock(real_url="https://wf1/test"), (), status=400)
    prepare.return_value = submission([1, 2], [])
    api.post_forecasts.side_effect = error
    if failure == "lookup":
        prepare.side_effect = RuntimeError("WF1 unavailable")
    elif failure == "post":
        api.post_forecasts.side_effect = RuntimeError("WF1 unavailable")
    elif failure == "retry_lookup":
        prepare.side_effect = [submission([1, 2], []), RuntimeError("WF1 unavailable")]
    elif failure == "retry_post":
        prepare.side_effect = [submission([1, 2], []), submission([2], [1])]

    response = client.post(morecast_v2_post_url, json=forecast_batch())

    assert response.status_code == 500
    assert response.json()["detail"] == app.routers.morecast_v2.WF1_ERROR_MESSAGE
    save.assert_not_called()
    log_error.assert_called_once()
    logged_error = log_error.call_args.kwargs["exc_info"]
    assert isinstance(logged_error, Exception)
    assert log_error.call_args.kwargs["extra"]["forecast_count"] == 2
    chatops.assert_called_once_with(log_error.call_args.args[0], logged_error)


@pytest.mark.parametrize("notification_result", [None, RuntimeError("ChatOps unavailable")])
def test_chatops_failure_preserves_submission_error(
    client, publishing, chatops, notification_result
):
    api, prepare, save, _cache = publishing
    prepare.return_value = submission([1, 2], [])
    api.post_forecasts.side_effect = RuntimeError("WF1 unavailable")
    if isinstance(notification_result, Exception):
        chatops.side_effect = notification_result
    else:
        chatops.return_value = notification_result

    response = client.post(morecast_v2_post_url, json=forecast_batch())

    assert response.status_code == 500
    assert response.json()["detail"] == app.routers.morecast_v2.WF1_ERROR_MESSAGE
    chatops.assert_called_once()
    save.assert_not_called()


def test_wf1_failure_produces_one_detailed_sentry_event(publishing, chatops):
    class InMemoryTransport(Transport):
        def __init__(self):
            super().__init__()
            self.events = []

        def capture_envelope(self, envelope):
            self.events.extend(item.get_event() for item in envelope.items if item.type == "event")

    transport = InMemoryTransport()
    api, prepare, save, _cache = publishing
    prepare.return_value = submission([1, 2], [])
    api.post_forecasts.side_effect = aiohttp.ClientResponseError(
        Mock(real_url="https://wf1/test"),
        (),
        status=400,
        message="Bad Request: ORA-00001: unique constraint violated",
    )

    with (
        sentry_sdk.Client(
            dsn="https://public@example.com/1",
            transport=transport,
            default_integrations=False,
            auto_enabling_integrations=False,
            integrations=[LoggingIntegration(), StarletteIntegration(), FastApiIntegration()],
            include_local_variables=False,
        ) as sentry_client,
        sentry_sdk.isolation_scope() as scope,
    ):
        scope.set_client(sentry_client)
        # build the app after sentry is enabled so its exception handling is covered too
        test_app = FastAPI()
        test_app.include_router(app.routers.morecast_v2.router, prefix="/api")
        with TestClient(test_app) as test_client:
            response = test_client.post(morecast_v2_post_url, json=forecast_batch())

    assert response.status_code == 500
    assert len(transport.events) == 1
    event = transport.events[0]
    assert event["extra"]["forecast_count"] == 2
    assert event["extra"]["wf1_status"] == 400
    exception = event["exception"]["values"][-1]
    assert exception["type"] == "ClientResponseError"
    assert "ORA-00001" in exception["value"]
    chatops.assert_called_once()
    save.assert_not_called()


def test_post_forecasts_by_date_range_unauthorized(client: TestClient):
    """forecast role required for persisting a forecast"""
    response = client.post(morecast_v2_post_by_date_range_url, json=[])
    assert response.status_code == 401


def test_post_forecast_by_date_range_authorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(morecast_v2_post_by_date_range_url, json=stations.model_dump())
    assert response.status_code == 200


def test_get_yesterday_dailies_unauthorized(client: TestClient):
    """user must be authenticated to retrieve yesterday dailies"""
    response = client.post(
        morecast_v2_post_yesterday_dailies_url, json={"station_codes": [209, 211, 302]}
    )
    assert response.status_code == 401


def test_get_yesterday_dailies_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """user must be authenticated to retrieve yesterday dailies"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    requested_station_codes = [209, 211, 302]

    response = client.post(
        morecast_v2_post_yesterday_dailies_url, json={"station_codes": requested_station_codes}
    )
    assert response.status_code == 200

    parsed_dailies = [
        StationDailyFromWF1.model_validate(raw_daily)
        for raw_daily in response.json().get("dailies")
    ]
    assert len(parsed_dailies) == 3

    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    for requested_station_code, response in zip(requested_station_codes, parsed_dailies):
        assert requested_station_code == response.station_code
        assert response.utcTimestamp.tzname() == "UTC"
        assert response.utcTimestamp.year == today_date.year
        assert response.utcTimestamp.month == today_date.month
        assert response.utcTimestamp.day == today_date.day - 1
        assert response.utcTimestamp.hour == 20


def test_get_determinates_unauthorized(client: TestClient):
    response = client.post(
        morecast_v2_post_determinates_url, json={"station_codes": [209, 211, 302]}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_determinates_authorized(
    anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    response = await async_client.post(
        morecast_v2_post_determinates_url, json={"stations": [209, 211, 302]}
    )
    assert response.status_code == 200
