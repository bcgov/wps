""" Test the health endpoint
"""
import os
import json
import requests
from starlette.testclient import TestClient
import app.main
from app.tests.common import MockResponse


def test_health_ok():
    """ Test health endpoint, given that everything is fine """
    client = TestClient(app.main.app)
    response = client.get('/health/')
    assert response.json().get('healthy')


def test_health_fail(monkeypatch):
    """ Test the health endpoint, given that pods aren't up """

    # pylint: disable=unused-argument
    def mock_requests_fail_condition(*args, **kwargs):
        """ Mock request response """
        fixture_path = ('fixtures/console.pathfinder.gov.bc.ca:8443/apis/'
                        'apps/v1beta1/namespaces/project_namespace/'
                        'statefulsets/some_suffix_fail.json')
        fixture_path = os.path.join(os.path.dirname(__file__), fixture_path)
        with open(fixture_path, 'r') as fixture_file:
            return MockResponse(json=json.load(fixture_file))

    monkeypatch.setattr(requests, 'get', mock_requests_fail_condition)

    client = TestClient(app.main.app)
    response = client.get('/health/')
    assert not response.json().get('healthy')
