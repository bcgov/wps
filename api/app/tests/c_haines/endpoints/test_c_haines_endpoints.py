"""BDD tests for c-haines api endpoint."""

from typing import Callable, AsyncGenerator, Optional
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
import pytest
import app.main
import app.routers.c_haines
import app.c_haines.fetch
from app.tests import _load_json_file, get_complete_filename
from wps_shared.tests.common import DefaultMockAioBaseClient


def _load_text_file(module_path: str, filename: str) -> Optional[str]:
    """Load json file given a module path and a filename"""
    if filename == "None":  # Not the best solution...
        return None
    if filename:
        with open(get_complete_filename(module_path, filename)) as file_pointer:
            return file_pointer.read()
    return None


def load_expected_response(module_path: str) -> Callable[[str], object]:
    """Return a loader for the expected response (dict is json, otherwise text)"""

    def _loader(filename: str):
        if filename and filename.endswith(".json"):
            return {"type": "json", "data": _load_json_file(module_path, filename)}
        return {"type": "text", "data": _load_text_file(module_path, filename)}

    return _loader


@pytest.fixture()
def mock_get_s3_client(monkeypatch):
    """Mock getting the s3 client"""

    @asynccontextmanager
    async def _mock_get_client_for_router() -> AsyncGenerator[DefaultMockAioBaseClient, str]:
        mock_aio_base_client = DefaultMockAioBaseClient("some_endpoint")
        mock_aio_base_client.mock_generate_presigned_url = "https://some.mock.url"
        mock_aio_base_client.mock_list_objects_v2_lookup = {
            "c-haines-polygons/kml/GDPS/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/kml/GDPS/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/kml/GDPS/2021/"}],
                "KeyCount": 1,
            },
            "c-haines-polygons/json/GDPS/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/GDPS/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/json/GDPS/2021/"}],
                "KeyCount": 1,
            },
            "c-haines-polygons/json/GDPS/2021/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/GDPS/2021/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/json/GDPS/2021/5/"}, {"Prefix": "c-haines-polygons/json/GDPS/2021/6/"}],
                "KeyCount": 2,
            },
            "c-haines-polygons/kml/GDPS/2021/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/kml/GDPS/2021/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/kml/GDPS/2021/5/"}, {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/"}],
                "KeyCount": 2,
            },
            "c-haines-polygons/json/GDPS/2021/6/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/GDPS/2021/6/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/1/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/2/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/3/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/4/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/5/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/6/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/7/"},
                    {"Prefix": "c-haines-polygons/json/GDPS/2021/6/8/"},
                ],
                "KeyCount": 8,
            },
            "c-haines-polygons/kml/GDPS/2021/6/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/kml/GDPS/2021/6/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/1/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/2/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/3/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/4/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/5/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/6/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/7/"},
                    {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/8/"},
                ],
                "KeyCount": 8,
            },
            "c-haines-polygons/json/GDPS/2021/6/8/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/GDPS/2021/6/8/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/json/GDPS/2021/6/8/0/"}, {"Prefix": "c-haines-polygons/json/GDPS/2021/6/8/12/"}],
                "KeyCount": 2,
            },
            "c-haines-polygons/kml/GDPS/2021/6/8/": {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/kml/GDPS/2021/6/8/",
                "Delimiter": "/",
                "MaxKeys": 1000,
                "CommonPrefixes": [{"Prefix": "c-haines-polygons/kml/GDPS/2021/6/8/0/"}, {"Prefix": "c-haines-polygons/kml/GDPS/2021/6/8/12/"}],
                "KeyCount": 2,
            },
        }
        yield mock_aio_base_client, "some_bucket"

    @asynccontextmanager
    async def _mock_get_client_list_objects() -> AsyncGenerator[DefaultMockAioBaseClient, str]:
        mock_aio_base_client = DefaultMockAioBaseClient("some_endpoint")
        mock_aio_base_client.mock_list_objects_v2_lookup = {
            "c-haines-polygons/json/GDPS/2021/6/8/": {
                "ResponseMetadata": {
                    "HTTPStatusCode": 200,
                },
                "IsTruncated": False,
                "Contents": [
                    {
                        "Key": "c-haines-polygons/json/GDPS/2021/6/8/12/2021-06-09T00:00:00.json",
                        "LastModified": "2021-06-09T04:01:24.467000+00:00",
                        "ETag": '"ade03d4476ef91e127e82523267aa620"',
                        "Size": 124774,
                        "StorageClass": "STANDARD",
                    },
                    {
                        "Key": "c-haines-polygons/json/GDPS/2021/6/8/12/2021-06-09T03:00:00.json",
                        "LastModified": "2021-06-09T04:27:57.679000+00:00",
                        "ETag": '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        "Size": 113355,
                        "StorageClass": "STANDARD",
                    },
                ],
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/GDPS/2021/6/8/",
                "MaxKeys": 1000,
                "EncodingType": "url",
                "KeyCount": 2,
            },
            "c-haines-polygons/json/RDPS/2021/6/8/": {
                "ResponseMetadata": {
                    "HTTPStatusCode": 200,
                },
                "IsTruncated": False,
                "Contents": [
                    {
                        "Key": "c-haines-polygons/json/RDPS/2021/6/8/0/2021-06-09T00:00:00.json",
                        "LastModified": "2021-06-09T04:01:24.467000+00:00",
                        "ETag": '"ade03d4476ef91e127e82523267aa620"',
                        "Size": 124774,
                        "StorageClass": "STANDARD",
                    },
                    {
                        "Key": "c-haines-polygons/json/RDPS/2021/6/8/0/2021-06-09T03:00:00.json",
                        "LastModified": "2021-06-09T04:27:57.679000+00:00",
                        "ETag": '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        "Size": 113355,
                        "StorageClass": "STANDARD",
                    },
                ],
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/RDPS/2021/6/8/",
                "MaxKeys": 1000,
                "EncodingType": "url",
                "KeyCount": 2,
            },
            "c-haines-polygons/json/HRDPS/2021/6/8/": {
                "ResponseMetadata": {
                    "HTTPStatusCode": 200,
                },
                "IsTruncated": False,
                "Contents": [],
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/json/HRDPS/2021/6/8/",
                "MaxKeys": 1000,
                "EncodingType": "url",
                "KeyCount": 0,
            },
            "c-haines-polygons/json/GDPS/2021/6/7/": {"Contents": []},
            "c-haines-polygons/json/RDPS/2021/6/7/": {"Contents": []},
            "c-haines-polygons/json/HRDPS/2021/6/7/": {"Contents": []},
            "c-haines-polygons/kml/GDPS/2021/6/8/12": {
                "ResponseMetadata": {
                    "HTTPStatusCode": 200,
                },
                "IsTruncated": False,
                "Contents": [
                    {
                        "Key": "c-haines-polygons/kml/GDPS/2021/6/8/12/2021-06-09T00:00:00.kml",
                        "LastModified": "2021-06-09T04:01:24.467000+00:00",
                        "ETag": '"ade03d4476ef91e127e82523267aa620"',
                        "Size": 124774,
                        "StorageClass": "STANDARD",
                    },
                    {
                        "Key": "c-haines-polygons/kml/GDPS/2021/6/8/12/2021-06-09T03:00:00.kml",
                        "LastModified": "2021-06-09T04:27:57.679000+00:00",
                        "ETag": '"9a60a4a94489915dc4dd4d5eb9f24435"',
                        "Size": 113355,
                        "StorageClass": "STANDARD",
                    },
                ],
                "Name": "gpdqha",
                "Prefix": "c-haines-polygons/kml/GDPS/2021/6/8/12",
                "MaxKeys": 1000,
                "EncodingType": "url",
                "KeyCount": 2,
            },
        }
        yield mock_aio_base_client, "some_bucket"

    monkeypatch.setattr(app.routers.c_haines, "get_client", _mock_get_client_for_router)
    monkeypatch.setattr(app.c_haines.fetch, "get_client", _mock_get_client_list_objects)


@pytest.mark.parametrize(
    "endpoint,status_code,expected_response_file",
    [
        ("/api/c-haines/model-runs", 200, "model_runs_expected_response.json"),
        ("/api/c-haines/GDPS/predictions?response_format=KML", 200, "most_recent_predictions_kml_expected_response.kml"),
        ("/api/c-haines/GDPS/predictions?response_format=KML&model_run_timestamp=2021-06-08T12%3A00%3A00", 200, "predictions_kml_expected_response.kml"),
        ("/api/c-haines/network-link", 200, "network-link_response.kml"),
    ],
)
@pytest.mark.usefixtures("mock_get_s3_client")
def test_chaines_endpoint(endpoint, status_code, expected_response_file):
    client = TestClient(app.main.app)
    # For the test, we set allow_redirects=False, so that we can test when we get a redirect.
    response = client.get(endpoint, follow_redirects=False)
    expected_response = load_expected_response(__file__)(expected_response_file) if expected_response_file is not None else None
    assert response.status_code == status_code
    if expected_response["type"] == "json":
        assert response.json() == expected_response["data"]
    else:
        # We don't always check the response, when it's a redirect we don't bother.
        if expected_response["data"] is not None:
            assert response.text == expected_response["data"]


@pytest.mark.parametrize(
    "endpoint,status_code,expected_response",
    [
        ("/api/c-haines/GDPS/prediction?model_run_timestamp=2021-03-08T12%3A00%3A00&prediction_timestamp=2021-03-08T12%3A00%3A00&response_format=JSON", 307, b""),
        ("/api/c-haines/GDPS/prediction?model_run_timestamp=2021-03-08T12%3A00%3A00&prediction_timestamp=2021-03-08T12%3A00%3A00&response_format=KML", 307, b""),
        ("/api/c-haines/GDPS/predictions?response_format=JSON", 501, b'{"detail":"Not Implemented"}'),
    ],
)
@pytest.mark.usefixtures("mock_get_s3_client")
def test_chaines_endpoint_no_response(endpoint, status_code, expected_response):
    client = TestClient(app.main.app)
    response = client.get(endpoint, follow_redirects=False)
    assert response.status_code == status_code
    assert response.content == expected_response
