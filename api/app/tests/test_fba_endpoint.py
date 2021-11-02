""" BDD tests for API /hfi-calc/ """
from pytest_bdd import scenario, given, then
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from app.schemas.fba import FireCenterStation, FireCentre
from app.tests.common import default_mock_client_get
import app.main
from app.tests import load_json_file
import app.routers.hfi_calc
from app.tests.test_hfi_dailies import AsyncIter

fire_centers = AsyncIter([
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
])


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_fba_endpoint.feature', 'Get fire centres with their stations',
          example_converters=dict(
            status=int,
            expected_fire_centers=load_json_file(__file__)))
def test_fba_fire_centers():
    """ BDD Scenario. """


@given('I request all fire centres', target_fixture='response')
def given_fba_fire_centers_request(monkeypatch):
    """ Make /fba/ request using mocked out ClientSession.
    """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)

    # Create API client and get the response.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}

    return client.get('/api/fba/fire-centers/', headers=headers)


@then('the response status code is <status>')
def assert_status_code(response, status):
    """ Assert that we receive the expected status code """
    assert response.status_code == status


@then('the response contains the list of <expected_fire_centers>')
def assert_fire_centers_list(response, expected_fire_centers):
    """ Assert that the fire centers returned are what is from the middleware """
    assert response.json() == expected_fire_centers
