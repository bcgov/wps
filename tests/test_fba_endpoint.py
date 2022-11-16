""" BDD tests for API /hfi-calc/ """
from pytest_bdd import scenario, given, then, parsers
import pytest
from starlette.testclient import TestClient
from aiohttp import ClientSession
from tests.common import default_mock_client_get
import app.main
from tests import load_json_file
import app.routers.hfi_calc


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario('test_fba_endpoint.feature', 'Get fire centres with their stations')
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

    return dict(response=client.get('/api/fba/fire-centers/', headers=headers))


@then(parsers.parse('the response contains the list of {expected_fire_centers}'),
      converters={'expected_fire_centers': load_json_file(__file__)})
def assert_fire_centers_list(response, expected_fire_centers):
    """ Assert that the fire centers returned are what is from the middleware """
    assert response['response'].json() == expected_fire_centers
