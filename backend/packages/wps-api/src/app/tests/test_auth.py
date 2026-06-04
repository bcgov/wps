from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import app.main
import pytest
import wps_shared.auth as auth
from app.tests import load_json_file
from fastapi import HTTPException, status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from wps_shared.auth import authentication_required


@pytest.mark.parametrize(
    "token, status, endpoint, verb, payload",
    [
        (
            "Basic token",
            401,
            "/api/weather_models/GDPS/predictions/summaries/",
            "post",
            "test_auth_stations_payload.json",
        ),
        (
            "just_token",
            401,
            "/api/weather_models/GDPS/predictions/summaries/",
            "post",
            "test_auth_stations_payload.json",
        ),
        (
            "Bearer token",
            401,
            "/api/weather_models/GDPS/predictions/summaries/",
            "post",
            "test_auth_stations_payload.json",
        ),
        (
            "just_token",
            401,
            "/api/weather_models/GDPS/predictions/most_recent/",
            "post",
            "test_auth_stations_payload.json",
        ),
        (
            "Bearer token",
            401,
            "/api/weather_models/GDPS/predictions/most_recent/",
            "post",
            "test_auth_stations_payload.json",
        ),
        ("just_token", 401, "/api/stations/details/", "get", "test_auth_stations_payload.json"),
    ],
)
@pytest.mark.usefixtures("mock_client_session")
def test_unauthenticated_requests(token, status, endpoint, verb, payload, spy_access_logging):
    client = TestClient(app.main.app)
    payload = load_json_file(__file__)(payload)
    response = None
    if verb == "post":
        response = client.post(endpoint, headers={"Authorization": token}, json=payload)
    else:
        response = client.get(endpoint, headers={"Authorization": token})

    assert response.status_code == status
    spy_access_logging.assert_called_once_with(None, False, endpoint)


@pytest.mark.parametrize(
    "status, endpoint, verb, utc_time",
    [
        (200, "/api/weather_models/GDPS/predictions/summaries/", "post", 1618870929583),
        (200, "/api/weather_models/GDPS/predictions/most_recent/", "post", 1618870929583),
        (200, "/api/stations/details/", "get", 1618870929583),
    ],
)
@pytest.mark.usefixtures("mock_client_session")
@pytest.mark.usefixtures("mock_jwt_decode")
def test_authenticated_requests(status, endpoint, verb, utc_time, spy_access_logging, monkeypatch):
    def mock_get_utc_now():
        return datetime.fromtimestamp(utc_time / 1000, tz=timezone.utc)

    monkeypatch.setattr(app.routers.stations, "get_utc_now", mock_get_utc_now)
    client = TestClient(app.main.app)
    response = None
    if verb == "post":
        response = client.post(
            endpoint, headers={"Authorization": "Bearer token"}, json={"stations": [838]}
        )
    if verb == "get":
        response = client.get(endpoint, headers={"Authorization": "Bearer token"})

    assert response.status_code == status
    spy_access_logging.assert_called_once_with("test_username", True, endpoint)


FBA_PREFIXES = ["/api/fba"]


def is_fba_route(route):
    return any(route.path.startswith(prefix) for prefix in FBA_PREFIXES)


def get_non_fba_routes(app):
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute) and not is_fba_route(route):
            # Only include routes that require authentication (i.e., have dependencies)
            if any(
                dep.dependency is authentication_required for dep in route.dependant.dependencies
            ):
                for method in route.methods:
                    if method in {"GET", "POST"}:
                        routes.append((route.path, method))
    return routes


@pytest.mark.usefixtures("mock_test_idir_jwt_decode")
def test_non_fba_routes_blocked_for_test_guid():
    client = TestClient(app.main.app)
    routes = get_non_fba_routes(app.main.app)
    headers = {"Authorization": "Bearer token"}
    payload = {"stations": [838]}
    for path, method in routes:
        if method == "POST":
            response = client.post(path, headers=headers, json=payload)
        else:
            response = client.get(path, headers=headers)
        assert response.status_code == 401


@pytest.mark.anyio
async def test_forecaster_or_spot_owner_auth_allows_forecaster_without_db_lookup(monkeypatch):
    token = {"client_roles": ["morecast2_write_forecast"], "idir_username": "someone"}

    def fail_if_queried():
        raise AssertionError("forecaster role should not need a spot request lookup")

    monkeypatch.setattr("wps_shared.db.database.get_async_read_session_scope", fail_if_queried)

    result = await auth.auth_with_forecaster_role_or_spot_owner_required(42, token)

    assert result == token


@pytest.mark.anyio
async def test_forecaster_or_spot_owner_auth_allows_spot_owner(monkeypatch):
    session = SimpleNamespace()
    token = {"client_roles": [], "idir_username": "owner_idir"}
    get_spot_request = AsyncMock(return_value=SimpleNamespace(requestor_idir="OWNER_IDIR"))

    @asynccontextmanager
    async def session_scope():
        yield session

    monkeypatch.setattr("wps_shared.db.database.get_async_read_session_scope", session_scope)
    monkeypatch.setattr("wps_shared.db.crud.smurfi.get_spot_request_by_id", get_spot_request)

    result = await auth.auth_with_forecaster_role_or_spot_owner_required(42, token)

    assert result == token
    get_spot_request.assert_awaited_once_with(session, 42)


@pytest.mark.anyio
async def test_forecaster_or_spot_owner_auth_rejects_non_owner(monkeypatch):
    token = {"client_roles": [], "idir_username": "other_idir"}
    get_spot_request = AsyncMock(return_value=SimpleNamespace(requestor_idir="owner_idir"))

    @asynccontextmanager
    async def session_scope():
        yield SimpleNamespace()

    monkeypatch.setattr("wps_shared.db.database.get_async_read_session_scope", session_scope)
    monkeypatch.setattr("wps_shared.db.crud.smurfi.get_spot_request_by_id", get_spot_request)

    with pytest.raises(HTTPException) as exc:
        await auth.auth_with_forecaster_role_or_spot_owner_required(42, token)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_forecaster_or_spot_owner_auth_returns_404_for_missing_spot_request(monkeypatch):
    token = {"client_roles": [], "idir_username": "owner_idir"}
    get_spot_request = AsyncMock(return_value=None)

    @asynccontextmanager
    async def session_scope():
        yield SimpleNamespace()

    monkeypatch.setattr("wps_shared.db.database.get_async_read_session_scope", session_scope)
    monkeypatch.setattr("wps_shared.db.crud.smurfi.get_spot_request_by_id", get_spot_request)

    with pytest.raises(HTTPException) as exc:
        await auth.auth_with_forecaster_role_or_spot_owner_required(42, token)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
