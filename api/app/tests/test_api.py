""" Unit tests for API.
"""
import unittest

from starlette.testclient import TestClient

from app.main import app


class BasicTestCase(unittest.TestCase):
    """ Some basic unit tests. """

    def test_stations(self):
        """ Test that stations request returns 200/OK. """
        client = TestClient(app)
        response = client.get('/stations')
        self.assertEqual(response.status_code, 200)

    def test_percentile(self):
        """ Test that a request for percentiles return 200/OK. """
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

    def test_percentile_no_stations_errors(self):
        """ Test to check for empty stations array. If no stations are provided in the request,
        the expected behavious is to get back a 400 error. """
        client = TestClient(app)
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

    def test_percentile_no_invalid_year_errors(self):
        """ Test to check for invalid year range. If an invalid year range is specified, the requested
        behaviour is to get back a 400 error. """
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
                                       "start": 2004,
                                       "end": 2019
                                   }
                               })
        self.assertEqual(response.status_code, 400)
