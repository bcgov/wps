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
                               headers={'Content-Type': 'application/json'},
                               json={
                                   "stations": [
                                       "331",
                                       "328"
                                   ],
                                   "percentile": 90,
                                   "year_range": {
                                       "start": 2009,
                                       "end": 2019
                                   }
                               })
        self.assertEqual(response.status_code, 200)
