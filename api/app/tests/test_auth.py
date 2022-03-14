""" Functional testing for authentication """

from datetime import datetime, timezone
from aiohttp import ClientSession
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
import pytest
import app.auth
import app.main
from app.tests import load_json_file
from app.tests.common import default_mock_client_get


@scenario('test_auth.feature', 'Handling unauthenticated users')
def test_auth_1st_scenario():
    """ BDD Scenario #1. """


@given(parsers.parse(
    "I am an unauthenticated user {token} when I {verb} a protected {endpoint} with {payload}"),
    converters={'token': str, 'verb': str, 'endpoint': str, 'payload': load_json_file(__file__)},
    target_fixture='response')
def given_unauthenticated_user(monkeypatch, token: str, endpoint: str, verb: str, payload: dict):
    """ Request (post/get) {endpoint} request which is protected """
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    if verb == 'post':
        response = client.post(endpoint, headers={'Authorization': token}, json=payload)
    elif verb == 'get':
        response = client.get(endpoint, headers={'Authorization': token})
    else:
        raise NotImplementedError('unexpected verb', verb)
    return response


@then("Unauthenticated access audit logs are created", converters={'endpoint': str})
def no_access_is_logged(spy_access_logging, endpoint):
    """Access audit logs are created"""
    spy_access_logging.assert_called_once_with(None, False, endpoint)


@then(parsers.parse("I will get an error with {status} code"), converters={'status': int})
def status_code(response, status: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario("test_auth.feature", "Verifying authenticated users")
def test_auth_2nd_scenario():
    """ BDD Scenario #2. """


@then("Authenticated access audit logs are created")
def access_is_logged(spy_access_logging, endpoint):
    """Access audit logs are created"""
    spy_access_logging.assert_called_once_with("test_username", True, endpoint)


@given(parsers.parse("utc_time: {utc_time}"), converters={'utc_time': int})
def given_utc_time(monkeypatch, utc_time: int):
    """ Mock out utc time """
    def mock_get_utc_now():
        return datetime.fromtimestamp(utc_time / 1000, tz=timezone.utc)
    monkeypatch.setattr(app.routers.stations, 'get_utc_now', mock_get_utc_now)


@given(parsers.parse("I am an authenticated user when I {verb} a protected {endpoint}"),
       converters={'verb': str, 'endpoint': str},
       target_fixture='response_2')
def given_authenticated_user(monkeypatch, endpoint: str, verb: str):
    """ Request (post/get) {endpoint} request which is protected """
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    if verb == 'post':
        return client.post(
            endpoint, headers={'Authorization': 'Bearer token'}, json={"stations": []})
    if verb == 'get':
        return client.get(
            endpoint, headers={'Authorization': 'Bearer token'}, json={"stations": []})
    raise NotImplementedError('unexpected verb', verb)


@then(parsers.parse("I shouldn't get an unauthorized error {status} code"), converters={'status': int})
def status_code_2(response_2, status: int):
    """ Assert that we receive the expected status code """
    assert response_2.status_code == status
