""" Test the health endpoint
"""
# import requests
from starlette.testclient import TestClient
import app.main


def test_health_ok():
    """ Test health endpoint, given that everything is fine """
    client = TestClient(app.main.app)
    response = client.get('/health/')
    assert response.status_code == 200
