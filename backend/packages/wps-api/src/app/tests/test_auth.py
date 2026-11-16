from datetime import datetime, timezone

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from wps_shared.auth import authentication_required

import app.main


@pytest.mark.parametrize("token", ["Basic token", "just_token", "Bearer token"])
@pytest.mark.usefixtures("mock_client_session")
def test_unauthenticated_requests(token, spy_access_logging):
    endpoint = "/api/stations/details/"
    client = TestClient(app.main.app)
    response = client.get(endpoint, headers={"Authorization": token})

    assert response.status_code == 401
    spy_access_logging.assert_called_once_with(None, False, endpoint)


@pytest.mark.usefixtures("mock_client_session")
@pytest.mark.usefixtures("mock_jwt_decode")
def test_authenticated_requests(spy_access_logging, monkeypatch):
    def mock_get_utc_now():
        return datetime.fromtimestamp(1618870929583 / 1000, tz=timezone.utc)

    monkeypatch.setattr(app.routers.stations, "get_utc_now", mock_get_utc_now)
    endpoint = "/api/stations/details/"
    client = TestClient(app.main.app)
    response = client.get(endpoint, headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
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
