"""Tests for ECMWFGribDownloader."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from weather_model_jobs.ecmwf_downloader import ECMWFGribDownloader


@pytest.fixture
def model_datetime():
    return datetime(2024, 1, 15, 0, 0, 0)


@pytest.fixture
def downloader(model_datetime, tmp_path):
    return ECMWFGribDownloader(model_datetime, str(tmp_path))


class TestURLConstruction:
    def test_grib_url_00z(self, downloader):
        url = downloader.grib_url(0)
        assert (
            url
            == "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20240115/00z/ifs/0p25/oper/2024011500z-0h-oper-fc.grib2"
        )

    def test_grib_url_12z(self, tmp_path):
        dt = datetime(2024, 6, 20, 12, 0, 0)
        dl = ECMWFGribDownloader(dt, str(tmp_path))
        url = dl.grib_url(48)
        assert (
            url
            == "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20240620/12z/ifs/0p25/oper/2024062012z-48h-oper-fc.grib2"
        )

    def test_grib_url_various_hours(self, downloader):
        for fxx in [0, 3, 6, 24, 120, 240]:
            url = downloader.grib_url(fxx)
            assert f"-{fxx}h-" in url
            assert url.endswith(".grib2")

    def test_index_url_is_grib_url_plus_index(self, downloader):
        grib = downloader.grib_url(6)
        index = downloader.index_url(6)
        assert index == grib + ".index"


class TestIndexParsing:
    def _make_index_lines(self, params):
        """Create realistic JSON-per-line index content."""
        lines = []
        offset = 0
        for param in params:
            length = 50000
            lines.append(
                json.dumps({"param": param, "_offset": offset, "_length": length, "levtype": "sfc"})
            )
            offset += length
        return "\n".join(lines)

    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_fetch_index_parses_json_lines(self, mock_get, downloader):
        index_content = self._make_index_lines(["2t", "msl", "10u", "10v", "2d", "tp", "sp"])
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = index_content
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        messages = downloader._fetch_index(0)
        assert len(messages) == 7
        assert messages[0]["param"] == "2t"

    def test_filter_byte_ranges_selects_target_params(self, downloader):
        messages = [
            {"param": "2t", "_offset": 0, "_length": 50000},
            {"param": "msl", "_offset": 50000, "_length": 40000},
            {"param": "10u", "_offset": 90000, "_length": 50000},
            {"param": "10v", "_offset": 140000, "_length": 50000},
            {"param": "2d", "_offset": 190000, "_length": 50000},
            {"param": "tp", "_offset": 240000, "_length": 50000},
            {"param": "sp", "_offset": 290000, "_length": 30000},
        ]
        ranges = downloader._filter_byte_ranges(messages)
        # Should match: 2t, 10u, 10v, 2d, tp (5 of the default ECMWF_PARAMS)
        assert len(ranges) == 5
        # Verify byte range format (start, end) where end = offset + length - 1
        assert ranges[0] == (0, 49999)  # 2t
        assert ranges[1] == (90000, 139999)  # 10u

    def test_filter_byte_ranges_no_matches(self, downloader):
        messages = [
            {"param": "msl", "_offset": 0, "_length": 50000},
            {"param": "sp", "_offset": 50000, "_length": 30000},
        ]
        ranges = downloader._filter_byte_ranges(messages)
        assert ranges == []

    def test_filter_byte_ranges_custom_params(self, model_datetime, tmp_path):
        dl = ECMWFGribDownloader(model_datetime, str(tmp_path), params=["2t", "tp"])
        messages = [
            {"param": "2t", "_offset": 0, "_length": 50000},
            {"param": "10u", "_offset": 50000, "_length": 50000},
            {"param": "tp", "_offset": 100000, "_length": 50000},
        ]
        ranges = dl._filter_byte_ranges(messages)
        assert len(ranges) == 2


class TestRetryBehavior:
    @patch("weather_model_jobs.ecmwf_downloader.time.sleep")
    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_retry_on_503(self, mock_get, mock_sleep, downloader):
        # First two calls return 503, third succeeds
        resp_503 = MagicMock()
        resp_503.status_code = 503

        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.text = json.dumps({"param": "2t", "_offset": 0, "_length": 100})
        resp_ok.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_503, resp_503, resp_ok]

        response = downloader._request_with_retry("http://example.com")
        assert response.status_code == 200
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("weather_model_jobs.ecmwf_downloader.time.sleep")
    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_retry_on_connection_error(self, mock_get, mock_sleep, downloader):
        mock_get.side_effect = [
            requests.ConnectionError("connection refused"),
            MagicMock(status_code=200),
        ]

        response = downloader._request_with_retry("http://example.com")
        assert response.status_code == 200
        assert mock_get.call_count == 2

    @patch("weather_model_jobs.ecmwf_downloader.time.sleep")
    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_raises_after_max_retries(self, mock_get, mock_sleep, downloader):
        mock_get.side_effect = requests.ConnectionError("connection refused")

        with pytest.raises(requests.ConnectionError):
            downloader._request_with_retry("http://example.com")
        assert mock_get.call_count == 3


class TestDownload:
    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_returns_none_on_404(self, mock_get, downloader):
        resp_404 = MagicMock()
        resp_404.status_code = 404
        http_error = requests.HTTPError(response=resp_404)
        resp_404.raise_for_status.side_effect = http_error
        mock_get.return_value = resp_404

        result = downloader.download(999)
        assert result is None

    @patch("weather_model_jobs.ecmwf_downloader.requests.get")
    def test_download_success(self, mock_get, downloader, tmp_path):
        # Mock index response
        index_content = "\n".join(
            [
                json.dumps({"param": "2t", "_offset": 0, "_length": 100}),
                json.dumps({"param": "2d", "_offset": 100, "_length": 100}),
            ]
        )
        resp_index = MagicMock()
        resp_index.status_code = 200
        resp_index.text = index_content
        resp_index.raise_for_status = MagicMock()

        # Mock range download responses
        resp_range = MagicMock()
        resp_range.status_code = 206
        resp_range.content = b"\x00" * 100
        resp_range.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_index, resp_range, resp_range]

        result = downloader.download(6)
        assert result is not None
        assert result.endswith(".grib2")
        assert "ecmwf_2024011500_006.grib2" in result
