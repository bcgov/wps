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
import time
from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit

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
        self._attempts: Counter[str] = Counter()
        self._connection_failures: Counter[str] = Counter()
        self._seconds_lost: Counter[str] = Counter()

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
            host = urlsplit(url).netloc
            self._attempts[host] += 1
            started = time.monotonic()
            try:
                response = self._session.get(url, timeout=self._timeout)
            except requests.RequestException as exc:
                # Not a warning: a single host failing is the case the fallback exists to
                # handle. The run-level summary reports how often it happened.
                self._connection_failures[host] += 1
                self._seconds_lost[host] += time.monotonic() - started
                logger.debug("Connection failed for %s: %s", url, exc)
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

    def log_connection_summary(self) -> None:
        """Log per-host connection failures for the requests made so far.

        A host failing every attempt means we paid the full timeout on each one, which is
        the difference between a slow run and a run that never finishes in its window.
        """
        for host, attempts in self._attempts.items():
            failures = self._connection_failures[host]
            if not failures:
                continue
            logger.warning(
                "%s: %d/%d requests failed to connect, %.0f seconds spent on timeouts",
                host,
                failures,
                attempts,
                self._seconds_lost[host],
            )
