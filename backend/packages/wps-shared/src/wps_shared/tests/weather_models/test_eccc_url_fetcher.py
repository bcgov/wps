"""Tests for ECCCUrlFetcher."""

from datetime import datetime
from unittest.mock import MagicMock

import aiohttp
import pytest

from wps_shared.weather_models.eccc_url_fetcher import ECCCUrlFetcher

# now=08:00 UTC, model_run_hour=0 — no date rollback needed
NOW = datetime(2026, 6, 23, 8, 0, 0)
MODEL_RUN_HOUR = 0

DD_URL = (
    "https://dd.weather.gc.ca/today/model_rdps/10km/00/001/"
    "20260623T00Z_MSC_RDPS_TMP_AGL-2m_RLatLon0.09_PT001H.grib2"
)
HPFX_URL = (
    "https://hpfx.collab.science.gc.ca/20260623/WXO-DD/model_rdps/10km/00/001/"
    "20260623T00Z_MSC_RDPS_TMP_AGL-2m_RLatLon0.09_PT001H.grib2"
)


class _FakeResponse:
    """Minimal stand-in for aiohttp.ClientResponse, usable as `async with ... as response:`."""

    def __init__(self, status: int, body: bytes = b""):
        self.status = status
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    @property
    def content(self):
        return self

    async def iter_chunked(self, chunk_size):
        if self._body:
            yield self._body

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientResponseError(MagicMock(), (), status=self.status)


def _resp(status: int, body: bytes = b"") -> _FakeResponse:
    return _FakeResponse(status, body)


def _fetcher(now=NOW, hour=MODEL_RUN_HOUR) -> ECCCUrlFetcher:
    return ECCCUrlFetcher(now, hour)


class TestCandidates:
    def test_hpfx_is_first(self):
        assert _fetcher().candidates(DD_URL)[0] == HPFX_URL

    def test_dd_is_last(self):
        assert _fetcher().candidates(DD_URL)[-1] == DD_URL

    def test_hpfx_url_substitutes_today_segment(self):
        url = _fetcher(datetime(2026, 1, 5, 8), 0)._to_hpfx(
            "https://dd.weather.gc.ca/today/model_gdps/15km/00/000/file.grib2"
        )
        assert (
            url
            == "https://hpfx.collab.science.gc.ca/20260105/WXO-DD/model_gdps/15km/00/000/file.grib2"
        )

    def test_date_rolls_back_when_now_is_before_model_run_hour(self):
        # 10:00 UTC querying the 12Z run — file date is yesterday
        f = _fetcher(datetime(2026, 6, 23, 10, 0, 0), 12)
        assert "/20260622/" in f._to_hpfx(DD_URL)

    def test_date_does_not_roll_back_when_now_is_at_or_after_model_run_hour(self):
        f = _fetcher(datetime(2026, 6, 23, 12, 0, 0), 12)
        assert "/20260623/" in f._to_hpfx(DD_URL)


class TestFetch:
    pytestmark = pytest.mark.anyio

    def _fetcher_with_responses(self, responses) -> ECCCUrlFetcher:
        f = _fetcher()
        f._session = MagicMock()
        f._session.get.side_effect = responses
        return f

    async def test_returns_true_and_writes_body_on_success(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(200, b"grib bytes")])
        result = await f.fetch(DD_URL, str(target))
        assert result is True
        assert target.read_bytes() == b"grib bytes"
        f._session.get.assert_called_once_with(HPFX_URL, timeout=aiohttp.ClientTimeout(total=60))

    async def test_falls_back_to_dd_on_hpfx_connection_error(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses(
            [aiohttp.ClientConnectionError("HPFX down"), _resp(200, b"data")]
        )
        result = await f.fetch(DD_URL, str(target))
        assert result is True
        assert f._session.get.call_count == 2

    async def test_falls_back_to_dd_on_hpfx_404(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(404), _resp(200, b"data")])
        result = await f.fetch(DD_URL, str(target))
        assert result is True
        assert f._session.get.call_count == 2

    async def test_falls_back_to_dd_on_hpfx_5xx(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(503), _resp(200, b"data")])
        assert await f.fetch(DD_URL, str(target)) is True

    async def test_returns_false_when_all_candidates_404(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(404), _resp(404)])
        assert await f.fetch(DD_URL, str(target)) is False

    async def test_raises_connection_error_when_all_candidates_fail(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses(
            [aiohttp.ClientConnectionError(), aiohttp.ClientConnectionError()]
        )
        with pytest.raises(aiohttp.ClientConnectionError):
            await f.fetch(DD_URL, str(target))

    async def test_raises_http_error_when_last_candidate_returns_5xx(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(404), _resp(503)])
        with pytest.raises(aiohttp.ClientResponseError):
            await f.fetch(DD_URL, str(target))

    async def test_custom_timeout_is_passed_to_session(self, tmp_path):
        target = tmp_path / "out.grib2"
        f = ECCCUrlFetcher(NOW, MODEL_RUN_HOUR, timeout=30)
        f._session = MagicMock()
        f._session.get.return_value = _resp(200, b"data")
        await f.fetch(DD_URL, str(target))
        f._session.get.assert_called_once_with(HPFX_URL, timeout=aiohttp.ClientTimeout(total=30))

    async def test_custom_session_is_used(self, tmp_path):
        target = tmp_path / "out.grib2"
        session = MagicMock()
        session.get.return_value = _resp(200, b"data")
        await ECCCUrlFetcher(NOW, MODEL_RUN_HOUR, session=session).fetch(DD_URL, str(target))
        session.get.assert_called_once()


class TestConnectionSummary:
    pytestmark = pytest.mark.anyio

    def _fetcher_with_responses(self, responses) -> ECCCUrlFetcher:
        f = _fetcher()
        f._session = MagicMock()
        f._session.get.side_effect = responses
        return f

    async def test_summarises_a_host_that_failed_every_attempt(self, caplog, tmp_path):
        """The case from the outage: hpfx unreachable, dd serving 404s."""
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([aiohttp.ClientConnectionError(), _resp(404)] * 2)
        await f.fetch(DD_URL, str(target))
        await f.fetch(DD_URL, str(target))

        with caplog.at_level("WARNING"):
            f.log_connection_summary()

        assert "hpfx.collab.science.gc.ca: 2/2 requests failed to connect" in caplog.text
        assert "dd.weather.gc.ca" not in caplog.text

    async def test_silent_when_no_connection_failures(self, caplog, tmp_path):
        target = tmp_path / "out.grib2"
        f = self._fetcher_with_responses([_resp(200, b"data")])
        await f.fetch(DD_URL, str(target))

        with caplog.at_level("WARNING"):
            f.log_connection_summary()

        assert caplog.text == ""
