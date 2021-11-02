""" BDD tests for API /hfi-calc/ """
from pytest_bdd import scenario, given, then
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from app.schemas.fba import FireCenterStation, FireCentre
from app.tests.common import default_mock_client_get
import app.main
import app.routers.hfi_calc

fire_centers = [
    FireCentre(
        id="1",
        name="Fire Center 1",
        stations=[FireCenterStation(code=1, name="s1", zone="k1"),
                  FireCenterStation(code=2, name="s2", zone="k1")]),
    FireCentre(
        id="2",
        name="Fire Center 2",
        stations=[FireCenterStation(code=3, name="s3", zone="k1"),
                  FireCenterStation(code=4, name="s4", zone="k1")])
]


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

    def mock_get_fire_centers(_: Session):
        return [fire_centers]

    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(app.wildfire_one.wfwx_api, 'get_fire_centers', mock_get_fire_centers)

    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    return client.get('/api/fba/fire-centers/', headers=headers)


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('the response contains the list of fire centers')
def assert_fire_centers_list(response):
    """ Assert that each fire centre returned has at least 1 planning area assigned to it """
    assert len(response.json()['fire_centers']) > 0
