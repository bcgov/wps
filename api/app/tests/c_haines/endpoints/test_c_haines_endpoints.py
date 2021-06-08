""" BDD tests for c-haines api endpoint.
"""
from typing import Callable, Generator, Union, Tuple
from contextlib import asynccontextmanager
from pytest_bdd import scenario, given, then
from fastapi.testclient import TestClient
import pytest
import app.main
import app.routers.c_haines
import app.c_haines.fetch
from app.tests import load_json_file, _load_json_file, get_complete_filename
from app.tests.common import DefaultMockAioBaseClient


def _load_text_file(module_path: str, filename: str) -> Union[str, None]:
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
        class MockAioBaseClient(DefaultMockAioBaseClient):
            """ Mock class with list objects """
            # It's a stubbed object, so we don't care about pylint warnings:
            # pylint: disable=unused-argument, missing-function-docstring, too-many-arguments, no-self-use

            async def list_objects(self, *args, **kwargs) -> dict:
                """ mock list objects """
                prefix = kwargs.get('Prefix')
                bucket_name = kwargs.get('Bucket')
                if prefix == 'c-haines-polygons/kml/GDPS/':
                    return {

                    }
                    # return iter([Object(bucket_name, prefix + '2019/'),
                    #              Object(bucket_name, prefix + '2020/'),
                    #              Object(bucket_name, prefix + '2021/')])
                return {}
                # return iter([Object(bucket_name, prefix + '1/'),
                #              Object(bucket_name, prefix + '2/'),
                #              Object(bucket_name, prefix + '3/')])
        mock_aio_base_client = MockAioBaseClient('some_endpoint')
        mock_aio_base_client.mock_get_presigned_url = 'https://some.mock.url'
        yield mock_aio_base_client, 'some_bucket'

    @asynccontextmanager
    async def _mock_get_client_list_objects() -> Generator[Tuple, None, None]:
        mock_minio = DefaultMockAioBaseClient('some_endpoint')
        mock_minio.mock_list_objects = {
            'Something': {}
        }
        #  iter(
        #     [
        #         Object('some_bucket', 'c-haines-polygons/kml/GDPS/2021/3/30/0/2021-04-01T19:00:00.kml'),
        #         Object('some_bucket', 'c-haines-polygons/kml/GDPS/2021/3/30/0/2021-04-01T21:00:00.kml')
        #     ])
        yield mock_minio, 'some_bucket'

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
        json.dump(collector['response'].text(), f)
    """
    if expected_response['type'] == 'json':
        assert collector['response'].json() == expected_response['data']
    else:
        # We don't always check the response, when it's a redirect we don't bother.
        if not expected_response['data'] is None:
            assert collector['response'].text == expected_response['data']
