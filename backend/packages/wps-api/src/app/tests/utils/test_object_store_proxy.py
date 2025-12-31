"""Tests for object store proxy router."""

import pytest
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
import app.main
from wps_shared.tests.common import DefaultMockAioBaseClient


@pytest.fixture()
def test_origin():
    """Fixture providing test origin for CORS."""
    return "http://localhost:3000"


@pytest.fixture()
def auth_headers(test_origin):
    """Fixture providing authentication and CORS headers."""
    return {"Authorization": "Bearer test-token", "Origin": test_origin}


@pytest.fixture()
def mock_s3_stream_and_head(monkeypatch):
    """Mock S3Client for HEAD and GET endpoints."""

    # Extend DefaultMockAioBaseClient to add head_object and get_object methods
    class ExtendedMockAioBaseClient(DefaultMockAioBaseClient):
        """Extended mock client with head_object and get_object methods."""

        async def head_object(self, **kwargs):
            """Mock head_object method."""
            key = kwargs.get("Key", "")

            if key == "test/file.tif":
                return {
                    "ContentType": "image/tiff",
                    "ContentLength": 1024,
                    "ResponseMetadata": {"HTTPStatusCode": 200},
                }
            elif key == "nonexistent.tif":
                error_response = {"Error": {"Code": "NoSuchKey"}}
                raise ClientError(error_response, "HeadObject")
            elif key == "forbidden.tif":
                error_response = {"Error": {"Code": "AccessDenied"}}
                raise ClientError(error_response, "HeadObject")
            elif key == "forbidden2.tif":
                error_response = {"Error": {"Code": "Forbidden"}}
                raise ClientError(error_response, "HeadObject")
            elif key == "s3error.tif":
                error_response = {"Error": {"Code": "InternalError"}}
                raise ClientError(error_response, "HeadObject")

            return {
                "ContentType": "application/octet-stream",
                "ContentLength": 2048,
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }

    # Replace the default mock with our extended version
    from wps_shared.tests.common import DefaultMockAioSession
    from contextlib import asynccontextmanager

    class ExtendedMockAioSession(DefaultMockAioSession):
        """Extended session that returns our extended client."""

        @asynccontextmanager
        async def create_client(self, *args, **kwargs):
            yield ExtendedMockAioBaseClient()

    def extended_aiobotocore_get_session():
        return ExtendedMockAioSession()

    import wps_shared.utils.s3_client

    monkeypatch.setattr(wps_shared.utils.s3_client, "get_session", extended_aiobotocore_get_session)

    # Mock for stream_object (used by GET endpoint)
    async def mock_stream_object(key: str, byte_range: str = None, chunk_size: int = 65536):
        """Mock stream_object static method."""

        # Full content response
        if key == "test/file.tif" and byte_range is None:

            async def content_generator():
                yield b"test content"

            s3_response = {
                "ContentType": "image/tiff",
                "ContentLength": 12,
                "ResponseMetadata": {"HTTPStatusCode": 200},
            }
            return content_generator(), s3_response

        # Range request response
        elif key == "test/file.tif" and byte_range:

            async def range_content_generator():
                yield b"test"

            s3_response = {
                "ContentType": "image/tiff",
                "ContentLength": 4,
                "ContentRange": "bytes 0-3/12",
                "ResponseMetadata": {"HTTPStatusCode": 206},
            }
            return range_content_generator(), s3_response

        # File not found
        elif key == "nonexistent.tif":
            error_response = {"Error": {"Code": "NoSuchKey"}}
            raise ClientError(error_response, "GetObject")

        # Access denied - test multiple error codes
        elif key == "forbidden.tif":
            error_response = {"Error": {"Code": "AccessDenied"}}
            raise ClientError(error_response, "GetObject")

        elif key == "forbidden2.tif":
            error_response = {"Error": {"Code": "Forbidden"}}
            raise ClientError(error_response, "GetObject")

        elif key == "forbidden3.tif":
            error_response = {"Error": {"Code": "403 Forbidden"}}
            raise ClientError(error_response, "GetObject")

        # S3 error
        elif key == "s3error.tif":
            error_response = {"Error": {"Code": "InternalError"}}
            raise ClientError(error_response, "GetObject")

        # Unexpected error
        elif key == "unexpectederror.tif":
            raise ValueError("Unexpected error occurred")

        # Default response for nested paths
        async def default_generator():
            yield b"default content"

        s3_response = {
            "ContentType": "application/octet-stream",
            "ContentLength": 15,
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }
        return default_generator(), s3_response

    # Patch stream_object
    monkeypatch.setattr("wps_shared.utils.s3_client.S3Client.stream_object", mock_stream_object)


class TestHeadS3Object:
    """Tests for the HEAD endpoint."""

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_head_success(self, auth_headers, test_origin):
        """Test successful HEAD request."""
        client = TestClient(app.main.app)
        response = client.head("/api/object-store-proxy/test/file.tif", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/tiff"
        assert response.headers["Content-Length"] == "1024"
        assert response.headers["Accept-Ranges"] == "bytes"
        # Verify CORS middleware is handling origin correctly
        assert response.headers["Access-Control-Allow-Origin"] == test_origin
        assert "Content-Length" in response.headers["Access-Control-Expose-Headers"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_head_not_found(self, auth_headers):
        """Test HEAD request for nonexistent file."""
        client = TestClient(app.main.app)
        response = client.head("/api/object-store-proxy/nonexistent.tif", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_head_forbidden_access_denied(self, auth_headers):
        """Test HEAD request for forbidden file (AccessDenied)."""
        client = TestClient(app.main.app)
        response = client.head("/api/object-store-proxy/forbidden.tif", headers=auth_headers)

        assert response.status_code == 403

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_head_forbidden_forbidden_code(self, auth_headers):
        """Test HEAD request for forbidden file (Forbidden code)."""
        client = TestClient(app.main.app)
        response = client.head("/api/object-store-proxy/forbidden2.tif", headers=auth_headers)

        assert response.status_code == 403

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_head_s3_error(self, auth_headers):
        """Test HEAD request with S3 error."""
        client = TestClient(app.main.app)
        response = client.head("/api/object-store-proxy/s3error.tif", headers=auth_headers)

        assert response.status_code == 502


class TestProxyS3Object:
    """Tests for the GET endpoint."""

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_success_full_content(self, auth_headers, test_origin):
        """Test successful GET request for full content."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/test/file.tif", headers=auth_headers)

        assert response.status_code == 200
        assert response.content == b"test content"
        assert response.headers["Content-Type"] == "image/tiff"
        assert response.headers["Content-Length"] == "12"
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.headers["Content-Disposition"] == "inline; filename=file.tif"
        # Verify CORS middleware is handling origin correctly
        assert response.headers["Access-Control-Allow-Origin"] == test_origin
        # Verify CORS expose headers
        exposed_headers = response.headers["Access-Control-Expose-Headers"]
        assert "Content-Length" in exposed_headers
        assert "Content-Type" in exposed_headers

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_success_range_request(self, auth_headers):
        """Test successful GET request with range header (partial content)."""
        client = TestClient(app.main.app)
        response = client.get(
            "/api/object-store-proxy/test/file.tif",
            headers={**auth_headers, "Range": "bytes=0-3"},
        )

        assert response.status_code == 206
        assert response.content == b"test"
        assert response.headers["Content-Type"] == "image/tiff"
        assert response.headers["Content-Range"] == "bytes 0-3/12"
        assert response.headers["Content-Length"] == "4"
        assert response.headers["Accept-Ranges"] == "bytes"

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_not_found(self, auth_headers):
        """Test GET request for nonexistent file."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/nonexistent.tif", headers=auth_headers)

        assert response.status_code == 404
        assert "object not found" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_forbidden_access_denied(self, auth_headers):
        """Test GET request for forbidden file (AccessDenied)."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/forbidden.tif", headers=auth_headers)

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_forbidden_forbidden_code(self, auth_headers):
        """Test GET request for forbidden file (Forbidden code)."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/forbidden2.tif", headers=auth_headers)

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_forbidden_403_code(self, auth_headers):
        """Test GET request for forbidden file (403 Forbidden code)."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/forbidden3.tif", headers=auth_headers)

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_s3_error(self, auth_headers):
        """Test GET request with S3 error."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/s3error.tif", headers=auth_headers)

        assert response.status_code == 502
        assert "Error fetching object from object store" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_unexpected_error(self, auth_headers):
        """Test GET request with unexpected error."""
        client = TestClient(app.main.app)
        response = client.get("/api/object-store-proxy/unexpectederror.tif", headers=auth_headers)

        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]

    @pytest.mark.usefixtures("mock_s3_stream_and_head", "mock_jwt_decode")
    def test_get_filename_extraction(self, auth_headers):
        """Test that filename is correctly extracted from path."""
        client = TestClient(app.main.app)
        response = client.get(
            "/api/object-store-proxy/path/to/nested/file.tif", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers["Content-Disposition"] == "inline; filename=file.tif"


class TestRangeStreamingResponse:
    """Tests for RangeStreamingResponse class."""

    def test_range_streaming_response_full_content(self):
        """Test RangeStreamingResponse with full content."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"test content"

        s3_response = {"ContentType": "image/tiff", "ContentLength": 12}

        response = RangeStreamingResponse(content_gen(), s3_response, "test.tif")

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/tiff"
        assert response.headers["Content-Length"] == "12"
        assert response.headers["Content-Disposition"] == "inline; filename=test.tif"
        assert response.headers["Accept-Ranges"] == "bytes"
        assert "Content-Range" not in response.headers

    def test_range_streaming_response_partial_content(self):
        """Test RangeStreamingResponse with partial content (range request)."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"test"

        s3_response = {
            "ContentType": "image/tiff",
            "ContentLength": 4,
            "ContentRange": "bytes 0-3/12",
        }

        response = RangeStreamingResponse(content_gen(), s3_response, "test.tif")

        assert response.status_code == 206
        assert response.headers["Content-Type"] == "image/tiff"
        assert response.headers["Content-Length"] == "4"
        assert response.headers["Content-Range"] == "bytes 0-3/12"
        assert response.headers["Accept-Ranges"] == "bytes"

    def test_range_streaming_response_default_content_type(self):
        """Test RangeStreamingResponse with missing ContentType."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"content"

        s3_response = {"ContentLength": 7}

        response = RangeStreamingResponse(content_gen(), s3_response, "file.bin")

        assert response.headers["Content-Type"] == "application/octet-stream"

    def test_range_streaming_response_cors_headers(self):
        """Test that CORS headers are properly set."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"content"

        s3_response = {"ContentType": "text/plain", "ContentLength": 7}

        response = RangeStreamingResponse(content_gen(), s3_response, "test.txt")

        # RangeStreamingResponse shouldn't set this header
        assert "Access-Control-Allow-Origin" not in response.headers
        exposed_headers = response.headers["Access-Control-Expose-Headers"]
        assert "Content-Length" in exposed_headers
        assert "Content-Range" in exposed_headers
        assert "Accept-Ranges" in exposed_headers
        assert "Content-Type" in exposed_headers

    def test_range_streaming_response_large_range(self):
        """Test RangeStreamingResponse with large byte range."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"large content chunk"

        s3_response = {
            "ContentType": "application/octet-stream",
            "ContentLength": 1000,
            "ContentRange": "bytes 500-1499/5000",
        }

        response = RangeStreamingResponse(content_gen(), s3_response, "large.bin")

        assert response.status_code == 206
        assert response.headers["Content-Length"] == "1000"
        assert response.headers["Content-Range"] == "bytes 500-1499/5000"

    def test_range_streaming_response_content_length_calculation(self):
        """Test that content length is correctly calculated from range."""
        from app.routers.object_store_proxy import RangeStreamingResponse

        async def content_gen():
            yield b"x" * 100

        s3_response = {
            "ContentType": "application/octet-stream",
            "ContentLength": 100,
            "ContentRange": "bytes 100-199/500",
        }

        response = RangeStreamingResponse(content_gen(), s3_response, "test.bin")

        # Range 100-199 should be 100 bytes
        assert response.headers["Content-Length"] == "100"
        assert response.status_code == 206
