""" BDD tests for API /hfi-calc/ """
from pytest_bdd import scenario, given, then
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from app.tests.common import default_mock_client_get
import app.main
import app.routers.hfi_calc


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_fba_endpoint.feature', 'Get fire centres with their stations',
          example_converters=dict(
              status=int,
              num_fire_centres=int))
def test_fba_fire_centers():
    """ BDD Scenario. """


@given('I request all fire centres', target_fixture='response')
def given_fba_fire_centers_request(monkeypatch):
    """ Make /fba/ request using mocked out ClientSession.
    """

    def mock_get_fire_weather_stations(_: Session):
        return []

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(app.wildfire_one.wfwx_api, 'get_fire_centers', mock_get_fire_weather_stations)

    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    return client.get('/api/fba/fire-centers/', headers=headers)


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status
