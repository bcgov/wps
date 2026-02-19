"""Downloads ECMWF IFS GRIB2 subsets using HTTP range requests.

Parses the S3-hosted .index file (JSON-per-line format) to identify byte ranges
for specific weather variables, then downloads only those bytes.
"""

import json
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

ECMWF_PARAMS = ["2t", "2d", "tp", "10u", "10v"]


class ECMWFGribDownloader:
    """Downloads ECMWF GRIB2 subsets from S3 using HTTP range requests."""

    BASE_URL = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"

    def __init__(self, model_datetime, save_dir: str, params: list[str] = ECMWF_PARAMS, max_retries: int = 3):
        """
        :param model_datetime: datetime of the model run (e.g. 2024-01-15 00:00 UTC)
        :param save_dir: directory to save downloaded GRIB files
        :param params: list of ECMWF parameter short names to download
        :param max_retries: maximum number of retry attempts for failed requests
        """
        self.model_datetime = model_datetime
        self.save_dir = save_dir
        self.params = params
        self.max_retries = max_retries

    def grib_url(self, fxx: int) -> str:
        """Construct the URL for a GRIB file at a given forecast hour."""
        date_str = self.model_datetime.strftime("%Y%m%d")
        hour_str = f"{self.model_datetime.hour:02d}z"
        step_str = f"{fxx}h"
        return f"{self.BASE_URL}/{date_str}/{hour_str}/ifs/0p25/oper/{date_str}{hour_str}-{step_str}-oper-fc.grib2"

    def index_url(self, fxx: int) -> str:
        """Construct the URL for the .index file corresponding to a GRIB file."""
        return self.grib_url(fxx) + ".index"

    def download(self, fxx: int) -> str | None:
        """Download a subset of a GRIB file for the given forecast hour.

        Returns the path to the downloaded file, or None if unavailable.
        """
        try:
            messages = self._fetch_index(fxx)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning("GRIB index not found for fxx=%d: %s", fxx, self.index_url(fxx))
                return None
            raise

        ranges = self._filter_byte_ranges(messages)
        if not ranges:
            logger.warning("No matching parameters found in index for fxx=%d", fxx)
            return None

        url = self.grib_url(fxx)
        dest = os.path.join(self.save_dir, f"ecmwf_{self.model_datetime.strftime('%Y%m%d%H')}_{fxx:03d}.grib2")
        self._download_ranges(url, ranges, dest)
        return dest

    def _fetch_index(self, fxx: int) -> list[dict]:
        """Fetch and parse the .index file (JSON-per-line format)."""
        url = self.index_url(fxx)
        response = self._request_with_retry(url)
        response.raise_for_status()

        messages = []
        for line in response.text.strip().splitlines():
            line = line.strip()
            if line:
                messages.append(json.loads(line))
        return messages

    def _filter_byte_ranges(self, messages: list[dict]) -> list[tuple[int, int]]:
        """Filter index messages to byte ranges for our target parameters."""
        ranges = []
        for msg in messages:
            if msg.get("param") in self.params:
                offset = msg["_offset"]
                length = msg["_length"]
                ranges.append((offset, offset + length - 1))
        return ranges

    def _download_ranges(self, url: str, ranges: list[tuple[int, int]], dest: str) -> None:
        """Download specific byte ranges from a URL and write to dest."""
        with open(dest, "wb") as f:
            for start, end in ranges:
                headers = {"Range": f"bytes={start}-{end}"}
                response = self._request_with_retry(url, headers=headers)
                response.raise_for_status()
                f.write(response.content)

    def _request_with_retry(self, url: str, headers: dict | None = None) -> requests.Response:
        """Make an HTTP GET request with retry logic for transient errors."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 503:
                    wait = 2**attempt
                    logger.warning("503 from %s, retrying in %ds (attempt %d/%d)", url, wait, attempt + 1, self.max_retries)
                    time.sleep(wait)
                    continue
                return response
            except requests.RequestException as e:
                last_exception = e
                wait = 2**attempt
                logger.warning("Request error for %s: %s, retrying in %ds (attempt %d/%d)", url, e, wait, attempt + 1, self.max_retries)
                time.sleep(wait)

        if last_exception:
            raise last_exception
        # All attempts got 503
        return response  # type: ignore[possibly-undefined]
