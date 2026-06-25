"""Resilient ECCC weather model file fetcher.

Tries HPFX first (10x bandwidth, best-effort uptime) then falls back to
dd.weather.gc.ca (standard bandwidth, 24/7 redundancy).

HPFX URL structure:  https://hpfx.collab.science.gc.ca/{YYYYMMDD}/WXO-DD/{model_path}
DD URL structure:    https://dd.weather.gc.ca/today/{model_path}

In the unlikely event HPFX is unavailable, dd.weather.gc.ca remains the
authoritative source with guaranteed 24/7 Internet redundancy.
"""

from __future__ import annotations

import logging
from datetime import datetime

import requests

from wps_shared.weather_models import adjust_model_day

logger = logging.getLogger(__name__)

_HPFX_BASE = "https://hpfx.collab.science.gc.ca"
_DD_TODAY_SEGMENT = "/today/"


class ECCCUrlFetcher:
    """
    Fetches ECCC GRIB2 files with automatic server fallback.

    Candidate order:
      1. hpfx.collab.science.gc.ca  — 10× bandwidth, best-effort uptime
      2. dd.weather.gc.ca           — standard bandwidth, 24/7 redundancy

    Parameters
    ----------
    now:
        Current UTC time (used together with model_run_hour to derive the run date).
    model_run_hour:
        The model run hour (e.g. 0, 6, 12, 18). When now.hour < model_run_hour the
        run date is rolled back one day, matching the behaviour of adjust_model_day.
    timeout:
        Per-request timeout in seconds.
    session:
        Optional shared requests.Session (caller owns lifecycle).
    """

    def __init__(
        self,
        now: datetime,
        model_run_hour: int,
        timeout: int = 60,
        session: requests.Session | None = None,
    ) -> None:
        self._date_str = adjust_model_day(now, model_run_hour).strftime("%Y%m%d")
        self._timeout = timeout
        self._session = session or requests.Session()

    def candidates(self, dd_url: str) -> list[str]:
        """Return the ordered list of URLs to try for *dd_url*."""
        return [self._to_hpfx(dd_url), dd_url]

    def _to_hpfx(self, dd_url: str) -> str:
        """Convert a dd.weather.gc.ca /today/ URL to its HPFX equivalent."""
        _, _, after_today = dd_url.partition(_DD_TODAY_SEGMENT)
        return f"{_HPFX_BASE}/{self._date_str}/WXO-DD/{after_today}"

    def get(self, dd_url: str) -> requests.Response | None:
        """
        Fetch *dd_url*, trying each candidate in priority order.

        Returns
        -------
        requests.Response
            The first successful (HTTP 200) response.
        None
            If every candidate returns HTTP 404 (file not yet published).

        Raises
        ------
        requests.HTTPError
            If the final candidate returns a non-404 HTTP error.
        requests.ConnectionError / requests.Timeout
            If every candidate raises a connection-level error and none succeed.
        """
        urls = self.candidates(dd_url)
        last_exc: Exception | None = None

        for url in urls:
            try:
                response = self._session.get(url, timeout=self._timeout)
            except requests.RequestException as exc:
                logger.warning("Connection failed for %s: %s", url, exc)
                last_exc = exc
                continue

            if response.status_code == 200:
                logger.info("Downloaded %s", url)
                return response

            if response.status_code == 404:
                logger.debug("404 %s", url)
                last_exc = None
                continue

            logger.warning("HTTP %d for %s", response.status_code, url)
            last_exc = requests.HTTPError(response=response)

        if last_exc is not None:
            raise last_exc

        return None
