"""Tests for SFMS daily FWI raster endpoints.

These endpoints are served by the standalone SFMS FWI service
(app.sfms_fwi_main), which is not publicly exposed. Authentication is
enforced by the APS Kong gateway (key-auth plugin). Tests verify routing,
S3 key construction, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock

import app.sfms_fwi_main
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

BASE_URL = "/api/sfms/daily-fwi"


@pytest.fixture()
def mock_stream_object(monkeypatch):
    """Mock S3Client.stream_object for streaming raster download tests."""

    async def _mock(key: str, byte_range: str = None, chunk_size: int = 65536):
        if "missing" in key:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        async def gen():
            yield b"fake-tif-content"

        return gen(), {"ContentType": "image/tiff", "ContentLength": 16}

    monkeypatch.setattr("wps_shared.utils.s3_client.S3Client.stream_object", _mock)


def _make_mock_dataset(extract_value=None):
    """Return a mock WPSDataset suitable for use as a context manager."""
    mock_ds = MagicMock()
    mock_ds.__enter__ = lambda s: s
    mock_ds.__exit__ = lambda s, *a: None
    mock_ds.extract_value_at_point.return_value = extract_value
    return mock_ds


class TestDailyFWIRasterDownload:
    """Tests for GET /sfms/daily-fwi/{for_date}/{parameter}."""

    @pytest.mark.usefixtures("mock_stream_object")
    def test_downloads_fwi_raster(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi")
        assert response.status_code == 200
        assert response.content == b"fake-tif-content"

    @pytest.mark.usefixtures("mock_stream_object")
    def test_downloads_each_parameter(self):
        client = TestClient(app.sfms_fwi_main.app)
        for param in ("dc", "dmc", "bui", "ffmc", "isi", "fwi"):
            response = client.get(f"{BASE_URL}/2025-11-02/{param}")
            assert response.status_code == 200, f"Expected 200 for parameter {param!r}"

    def test_returns_404_for_missing_raster(self, monkeypatch):
        async def _raise_not_found(key, byte_range=None, chunk_size=65536):
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        monkeypatch.setattr("wps_shared.utils.s3_client.S3Client.stream_object", _raise_not_found)
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi")
        assert response.status_code == 404

    @pytest.mark.usefixtures("mock_stream_object")
    def test_invalid_parameter_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/invalid_param")
        assert response.status_code == 422

    @pytest.mark.usefixtures("mock_stream_object")
    def test_uses_actual_run_type_in_s3_key(self, monkeypatch):
        captured_keys = []

        async def _capture_key(key, byte_range=None, chunk_size=65536):
            captured_keys.append(key)

            async def gen():
                yield b"data"

            return gen(), {"ContentType": "image/tiff", "ContentLength": 4}

        monkeypatch.setattr("wps_shared.utils.s3_client.S3Client.stream_object", _capture_key)
        client = TestClient(app.sfms_fwi_main.app)
        client.get(f"{BASE_URL}/2025-11-02/ffmc")
        assert len(captured_keys) == 1
        assert "sfms_ng" in captured_keys[0]
        assert "actual" in captured_keys[0]
        assert "ffmc_20251102.tif" in captured_keys[0]


class TestHourlyFFMCRasterDownload:
    """Tests for GET /sfms/daily-fwi/{for_date}/hffmc."""

    @pytest.mark.usefixtures("mock_stream_object")
    def test_downloads_hourly_ffmc_raster(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/hffmc?hour=12")
        assert response.status_code == 200
        assert response.content == b"fake-tif-content"

    def test_missing_hour_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/hffmc")
        assert response.status_code == 422

    def test_invalid_hour_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/hffmc?hour=25")
        assert response.status_code == 422

    @pytest.mark.usefixtures("mock_stream_object")
    def test_uses_hffmc_key_path(self, monkeypatch):
        captured_keys = []

        async def _capture_key(key, byte_range=None, chunk_size=65536):
            captured_keys.append(key)

            async def gen():
                yield b"data"

            return gen(), {"ContentType": "image/tiff", "ContentLength": 4}

        monkeypatch.setattr("wps_shared.utils.s3_client.S3Client.stream_object", _capture_key)
        client = TestClient(app.sfms_fwi_main.app)
        client.get(f"{BASE_URL}/2025-11-02/hffmc?hour=12")
        assert len(captured_keys) == 1
        assert "hourlies" in captured_keys[0]
        assert "fine_fuel_moisture_code" in captured_keys[0]


class TestDailyFWIValueAtPoint:
    """Tests for GET /sfms/daily-fwi/{for_date}/{parameter}/value."""

    def test_returns_value_at_point(self, monkeypatch):
        monkeypatch.setattr("app.routers.sfms_fwi.read_object", AsyncMock(return_value=b"fake-bytes"))
        monkeypatch.setattr("app.routers.sfms_fwi.WPSDataset.from_bytes", lambda b: _make_mock_dataset(42.5))

        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi/value?lat=49.0&lon=-123.0")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2025-11-02"
        assert data["parameter"] == "fwi"
        assert data["latitude"] == pytest.approx(49.0)
        assert data["longitude"] == pytest.approx(-123.0)

    def test_returns_null_value_when_outside_raster(self, monkeypatch):
        monkeypatch.setattr("app.routers.sfms_fwi.read_object", AsyncMock(return_value=b"fake-bytes"))
        monkeypatch.setattr("app.routers.sfms_fwi.WPSDataset.from_bytes", lambda b: _make_mock_dataset(None))

        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi/value?lat=0.0&lon=0.0")
        assert response.status_code == 200
        assert response.json()["value"] is None

    def test_returns_404_when_raster_missing(self, monkeypatch):
        async def _raise_not_found(key):
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        monkeypatch.setattr("app.routers.sfms_fwi.read_object", _raise_not_found)
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi/value?lat=49.0&lon=-123.0")
        assert response.status_code == 404

    def test_missing_lat_lon_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi/value")
        assert response.status_code == 422

    def test_invalid_parameter_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/notaparam/value?lat=49.0&lon=-123.0")
        assert response.status_code == 422

    def test_uses_actual_run_type_in_s3_key(self, monkeypatch):
        captured_keys = []

        async def _capture_key(key):
            captured_keys.append(key)
            return b"fake-bytes"

        monkeypatch.setattr("app.routers.sfms_fwi.read_object", _capture_key)
        monkeypatch.setattr("app.routers.sfms_fwi.WPSDataset.from_bytes", lambda b: _make_mock_dataset(42.5))

        client = TestClient(app.sfms_fwi_main.app)
        client.get(f"{BASE_URL}/2025-11-02/ffmc/value?lat=49.0&lon=-123.0")
        assert len(captured_keys) == 1
        assert "sfms_ng" in captured_keys[0]
        assert "actual" in captured_keys[0]
        assert "ffmc_20251102.tif" in captured_keys[0]


class TestHourlyFFMCValueAtPoint:
    """Tests for GET /sfms/daily-fwi/{for_date}/hffmc/value."""

    def test_returns_value_at_point(self, monkeypatch):
        monkeypatch.setattr("app.routers.sfms_fwi.read_object", AsyncMock(return_value=b"fake-bytes"))
        monkeypatch.setattr("app.routers.sfms_fwi.WPSDataset.from_bytes", lambda b: _make_mock_dataset(85.3))

        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/hffmc/value?hour=12&lat=49.0&lon=-123.0")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2025-11-02"
        assert data["parameter"] == "hffmc"
        assert data["latitude"] == pytest.approx(49.0)
        assert data["longitude"] == pytest.approx(-123.0)

    def test_missing_hour_returns_422(self):
        client = TestClient(app.sfms_fwi_main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/hffmc/value?lat=49.0&lon=-123.0")
        assert response.status_code == 422


class TestMainAPIDoesNotServeDailyFWI:
    """The daily FWI routes must only exist on the standalone service."""

    def test_main_api_returns_404_for_daily_fwi(self):
        import app.main

        client = TestClient(app.main.app)
        response = client.get(f"{BASE_URL}/2025-11-02/fwi")
        assert response.status_code == 404
