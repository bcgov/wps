"""Tests for ECCCUrlFetcher."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
import requests

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


def _resp(status: int) -> MagicMock:
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    return r


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


class TestGet:
    def _fetcher_with_responses(self, responses) -> ECCCUrlFetcher:
        f = _fetcher()
        f._session = MagicMock()
        f._session.get.side_effect = responses
        return f

    def test_returns_hpfx_response_on_success(self):
        f = self._fetcher_with_responses([_resp(200)])
        result = f.get(DD_URL)
        assert result is not None
        f._session.get.assert_called_once_with(HPFX_URL, timeout=60)

    def test_falls_back_to_dd_on_hpfx_connection_error(self):
        f = self._fetcher_with_responses([requests.ConnectionError("HPFX down"), _resp(200)])
        result = f.get(DD_URL)
        assert result is not None
        assert f._session.get.call_count == 2

    def test_falls_back_to_dd_on_hpfx_404(self):
        f = self._fetcher_with_responses([_resp(404), _resp(200)])
        result = f.get(DD_URL)
        assert result is not None
        assert f._session.get.call_count == 2

    def test_falls_back_to_dd_on_hpfx_5xx(self):
        f = self._fetcher_with_responses([_resp(503), _resp(200)])
        assert f.get(DD_URL) is not None

    def test_returns_none_when_all_candidates_404(self):
        f = self._fetcher_with_responses([_resp(404), _resp(404)])
        assert f.get(DD_URL) is None

    def test_raises_connection_error_when_all_candidates_fail(self):
        f = self._fetcher_with_responses([requests.ConnectionError(), requests.ConnectionError()])
        with pytest.raises(requests.ConnectionError):
            f.get(DD_URL)

    def test_raises_http_error_when_last_candidate_returns_5xx(self):
        f = self._fetcher_with_responses([_resp(404), _resp(503)])
        with pytest.raises(requests.HTTPError):
            f.get(DD_URL)

    def test_custom_timeout_is_passed_to_session(self):
        f = ECCCUrlFetcher(NOW, MODEL_RUN_HOUR, timeout=30)
        f._session = MagicMock()
        f._session.get.return_value = _resp(200)
        f.get(DD_URL)
        f._session.get.assert_called_once_with(HPFX_URL, timeout=30)

    def test_custom_session_is_used(self):
        session = MagicMock()
        session.get.return_value = _resp(200)
        ECCCUrlFetcher(NOW, MODEL_RUN_HOUR, session=session).get(DD_URL)
        session.get.assert_called_once()


class TestConnectionSummary:
    def _fetcher_with_responses(self, responses) -> ECCCUrlFetcher:
        f = _fetcher()
        f._session = MagicMock()
        f._session.get.side_effect = responses
        return f

    def test_summarises_a_host_that_failed_every_attempt(self, caplog):
        """The case from the outage: hpfx unreachable, dd serving 404s."""
        f = self._fetcher_with_responses([requests.ConnectionError(), _resp(404)] * 2)
        f.get(DD_URL)
        f.get(DD_URL)

        with caplog.at_level("WARNING"):
            f.log_connection_summary()

        assert "hpfx.collab.science.gc.ca: 2/2 requests failed to connect" in caplog.text
        assert "dd.weather.gc.ca" not in caplog.text

    def test_silent_when_no_connection_failures(self, caplog):
        f = self._fetcher_with_responses([_resp(200)])
        f.get(DD_URL)

        with caplog.at_level("WARNING"):
            f.log_connection_summary()

        assert caplog.text == ""
