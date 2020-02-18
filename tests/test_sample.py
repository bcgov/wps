import unittest

from starlette.responses import HTMLResponse
from starlette.testclient import TestClient

from main import app


class SampleTestCase(unittest.TestCase):

    def test_sample(self):
        client = TestClient(app)
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
