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
                                       "start": 2010,
                                       "end": 2019
                                   }
                               })
        self.assertEqual(response.status_code, 200)

    def test_percentile_errors(self):
        client = TestClient(app)

        # Test to check for empty stations array
        response = client.post('/percentiles/',
                               headers={'Content-Type': 'application/json'},
                               json={
                                   "stations": [
                                   ],
                                   "percentile": 90,
                                   "year_range": {
                                       "start": 2010,
                                       "end": 2019
                                   }
                               })
        self.assertEqual(response.status_code, 400)

        # Test to check for invalid year range
        response = client.post('/percentiles/',
                               headers={'Content-Type': 'application/json'},
                               json={
                                   "stations": [
                                       "331",
                                       "328"
                                   ],
                                   "percentile": 90,
                                   "year_range": {
                                       "start": 2004,
                                       "end": 2019
                                   }
                               })
        self.assertEqual(response.status_code, 400)
