import unittest

from starlette.responses import HTMLResponse
from starlette.testclient import TestClient

from main import app


class BasicTestCase(unittest.TestCase):

    def test_stations(self):
        client = TestClient(app)
        response = client.get('/stations')
        self.assertEqual(response.status_code, 200)

    def test_percentile(self):
        client = TestClient(app)
        response = client.post('/percentiles/',
                               headers={'Content-Type' : 'application/x-www-form-urlencoded'},
                               data='stations=331&percentile=90&start_year=2009&end_year=2019')
        self.assertEqual(response.status_code, 200)
