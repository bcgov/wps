""" BDD tests for c-haines api endpoint.
"""
from typing import Callable, Generator, Optional, Tuple
from contextlib import asynccontextmanager
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
import pytest
import app.main
import app.routers.c_haines
import app.c_haines.fetch
from app.tests import load_json_file, _load_json_file, get_complete_filename
from app.tests.common import DefaultMockAioBaseClient


def _load_text_file(module_path: str, filename: str) -> Optional[str]:
    """ Load json file given a module path and a filename """
    if filename:
        with open(get_complete_filename(module_path, filename)) as file_pointer:
            return file_pointer.read()
    return None


def load_expected_response(module_path: str) -> Callable[[str], object]:
    """ Return a loader for the expected response (dict is json, otherwise text) """
    def _loader(filename: str):
        if filename and filename.endswith('.json'):
            return {'type': 'json', 'data': _load_json_file(module_path, filename)}
        return {'type': 'text', 'data': _load_text_file(module_path, filename)}
    return _loader


@pytest.fixture()
def mock_get_s3_client(monkeypatch):
    """ Mock getting the s3 client """
    @asynccontextmanager
    async def _mock_get_client_for_router() -> Generator[Tuple, None, None]:
        mock_aio_base_client = DefaultMockAioBaseClient('some_endpoint')
        mock_aio_base_client.mock_generate_presigned_url = 'https://some.mock.url'
        mock_aio_base_client.mock_list_objects_v2_lookup = {
            'c-haines-polygons/kml/GDPS/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/kml/GDPS/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/'}
                ],
                'KeyCount': 1
            },
            'c-haines-polygons/json/GDPS/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/GDPS/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/'}
                ],
                'KeyCount': 1
            },
            'c-haines-polygons/json/GDPS/2021/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/GDPS/2021/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/5/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/'}
                ],
                'KeyCount': 2
            },
            'c-haines-polygons/kml/GDPS/2021/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/kml/GDPS/2021/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/5/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/'}
                ],
                'KeyCount': 2
            },
            'c-haines-polygons/json/GDPS/2021/6/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/GDPS/2021/6/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/1/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/2/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/3/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/4/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/5/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/6/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/7/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/8/'},
                ],
                'KeyCount': 8
            },
            'c-haines-polygons/kml/GDPS/2021/6/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/1/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/2/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/3/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/4/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/5/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/6/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/7/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/8/'},
                ],
                'KeyCount': 8
            },
            'c-haines-polygons/json/GDPS/2021/6/8/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/GDPS/2021/6/8/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/8/0/'},
                    {'Prefix': 'c-haines-polygons/json/GDPS/2021/6/8/12/'}
                ],
                'KeyCount': 2
            },
            'c-haines-polygons/kml/GDPS/2021/6/8/': {
                'ResponseMetadata':
                {
                    'HTTPStatusCode': 200
                },
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/8/',
                'Delimiter': '/',
                'MaxKeys': 1000,
                'CommonPrefixes': [
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/8/0/'},
                    {'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/8/12/'}
                ],
                'KeyCount': 2
            }
        }
        yield mock_aio_base_client, 'some_bucket'

    @asynccontextmanager
    async def _mock_get_client_list_objects() -> Generator[Tuple, None, None]:
        mock_aio_base_client = DefaultMockAioBaseClient('some_endpoint')
        mock_aio_base_client.mock_list_objects_v2_lookup = {
            'c-haines-polygons/json/GDPS/2021/6/8/': {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                },
                'IsTruncated': False,
                'Contents': [
                    {
                        'Key': 'c-haines-polygons/json/GDPS/2021/6/8/12/2021-06-09T00:00:00.json',
                        'LastModified': '2021-06-09T04:01:24.467000+00:00',
                        'ETag': '"ade03d4476ef91e127e82523267aa620"',
                        'Size': 124774,
                        'StorageClass': 'STANDARD'
                    },
                    {
                        'Key': 'c-haines-polygons/json/GDPS/2021/6/8/12/2021-06-09T03:00:00.json',
                        'LastModified': '2021-06-09T04:27:57.679000+00:00',
                        'ETag': '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        'Size': 113355,
                        'StorageClass': 'STANDARD'
                    }
                ],
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/GDPS/2021/6/8/',
                'MaxKeys': 1000,
                'EncodingType': 'url',
                'KeyCount': 2
            },
            'c-haines-polygons/json/RDPS/2021/6/8/': {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                },
                'IsTruncated': False,
                'Contents': [
                    {
                        'Key': 'c-haines-polygons/json/RDPS/2021/6/8/0/2021-06-09T00:00:00.json',
                        'LastModified': '2021-06-09T04:01:24.467000+00:00',
                        'ETag': '"ade03d4476ef91e127e82523267aa620"',
                        'Size': 124774,
                        'StorageClass': 'STANDARD'
                    },
                    {
                        'Key': 'c-haines-polygons/json/RDPS/2021/6/8/0/2021-06-09T03:00:00.json',
                        'LastModified': '2021-06-09T04:27:57.679000+00:00',
                        'ETag': '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        'Size': 113355,
                        'StorageClass': 'STANDARD'
                    }
                ],
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/RDPS/2021/6/8/',
                'MaxKeys': 1000,
                'EncodingType': 'url',
                'KeyCount': 2
            },
            'c-haines-polygons/json/HRDPS/2021/6/8/': {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                },
                'IsTruncated': False,
                'Contents': [],
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/json/HRDPS/2021/6/8/',
                'MaxKeys': 1000,
                'EncodingType': 'url',
                'KeyCount': 0
            },
            'c-haines-polygons/json/GDPS/2021/6/7/': {
                'Contents': []
            },
            'c-haines-polygons/json/RDPS/2021/6/7/': {
                'Contents': []
            },
            'c-haines-polygons/json/HRDPS/2021/6/7/': {
                'Contents': []
            },
            'c-haines-polygons/kml/GDPS/2021/6/8/12': {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                },
                'IsTruncated': False,
                'Contents': [
                    {
                        'Key': 'c-haines-polygons/kml/GDPS/2021/6/8/12/2021-06-09T00:00:00.kml',
                        'LastModified': '2021-06-09T04:01:24.467000+00:00',
                        'ETag': '"ade03d4476ef91e127e82523267aa620"',
                        'Size': 124774,
                        'StorageClass': 'STANDARD'
                    },
                    {
                        'Key': 'c-haines-polygons/kml/GDPS/2021/6/8/12/2021-06-09T03:00:00.kml',
                        'LastModified': '2021-06-09T04:27:57.679000+00:00',
                        'ETag': '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        'Size': 113355,
                        'StorageClass': 'STANDARD'
                    }
                ],
                'Name': 'gpdqha',
                'Prefix': 'c-haines-polygons/kml/GDPS/2021/6/8/12',
                'MaxKeys': 1000,
                'EncodingType': 'url',
                'KeyCount': 2
            }
        }
        yield mock_aio_base_client, 'some_bucket'

    monkeypatch.setattr(app.routers.c_haines, 'get_client', _mock_get_client_for_router)
    monkeypatch.setattr(app.c_haines.fetch, 'get_client', _mock_get_client_list_objects)


@pytest.mark.usefixtures('mock_get_s3_client')
@scenario("test_c_haines_endpoints.feature", "C-Haines endpoint testing",
          example_converters=dict(
              crud_mapping=load_json_file(__file__),
              endpoint=str,
              status_code=int,
              expected_response=load_expected_response(__file__)))
def test_c_haines():
    """ BDD Scenario for c-haines """


@given("I call <endpoint>", target_fixture='collector')
def given_endpoint(endpoint: str):
    """ Call the API endpoint and store the response """
    client = TestClient(app.main.app)
    # For the test, we set allow_redirects=False, so that we can test when we get a redirect.
    return {'response': client.get(endpoint, allow_redirects=False)}


@then("I expect <status_code>")
def then_status_code(collector, status_code: int):
    """ Assert that we receive the expected status code """
    assert collector['response'].status_code == status_code


@then("The <expected_response> is matched")
def then_expected_response(collector, expected_response):
    """ Assert that the response is as expected
    The expected response was saved by running this test, and then
    writing the response to file:

    # for json
    with open('expected_response.json', 'w') as f:
        json.dump(collector['response'].json(), f)
    # for kml
    with open('expected_response.kml', 'w') as f:
        f.write(collector['response'].text())
    """
    if expected_response['type'] == 'json':
        assert collector['response'].json() == expected_response['data']
    else:
        # We don't always check the response, when it's a redirect we don't bother.
        if not expected_response['data'] is None:
            assert collector['response'].text == expected_response['data']
