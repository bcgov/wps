""" Functional testing for authentication """
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from pytest_mock import MockerFixture
from unittest.mock import patch
from app.auth import authenticate

from app.db.crud.api_access_audits import create_api_access_audit_log
import pytest
import app.main


@scenario('test_auth.feature', 'Handling unauthenticated users',
          example_converters=dict(token=str, status=int, message=str, endpoint=str))
def test_auth_1st_scenario():
    """ BDD Scenario #1. """


@given("I am an unauthenticated user <token> when I access a protected <endpoint>", target_fixture='response')
def given_unauthenticated_user(monkeypatch, token: str, endpoint: str):
    """ Make POST {endpoint} request which is protected """
    def mock_audit_log:

    monkeypatch.setattr('app.db.crud.api_access_audits.create_api_access_audit_log', )
    client = TestClient(app.main.app)
    response = client.post(endpoint, headers={'Authorization': token})
    assert mock_access_log.called
    # with patch('app.db.crud.api_access_audits.create_api_access_audit_log') as mock_access_log:
    #     client = TestClient(app.main.app)
    #     response = client.post(endpoint, headers={'Authorization': token})
    #     assert mock_access_log.called
    return response


@then("I will get an error with <status> code")
def status_code(response, status: int):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then("I will see an error <message>")
def error_message(response, message: str):
    """ Assert that we receive the expected message """
    assert response.json()['detail'] == message


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario("test_auth.feature", "Verifying authenticated users", example_converters=dict(status=int))
def test_auth_2nd_scenario():
    """ BDD Scenario #2. """


@given("I am an authenticated user when I access a protected <endpoint>", target_fixture='response_2')
def given_authenticated_user(endpoint: str):
    """ Make POST {endpoint} request which is protected """
    client = TestClient(app.main.app)
    return client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={"stations": []})


@then("I shouldn't get an unauthorized error <status> code")
def status_code_2(response_2, status: int):
    """ Assert that we receive the expected status code """
    assert response_2.status_code == status


def test_auth_func():
    with patch('app.db.crud.api_access_audits.create_api_access_audit_log') as mock_access_log:
        assert mock_access_log.called
