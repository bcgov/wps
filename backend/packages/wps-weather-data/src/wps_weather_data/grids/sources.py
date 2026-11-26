"""Where each model's GRIB fields are published, and fetching one field from there.

MSC publishes a file per field. NOAA and ECMWF publish every field of a forecast hour in one file
of hundreds of MB, with an index beside it saying where each field is, so one field is fetched as
a range of bytes.
"""

import http.client
import json
import random
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Protocol

TIMEOUT_SECONDS = 60
ATTEMPTS = 5
# The source is busy or briefly failing. AWS and Google answer 503 when asked too fast.
RETRIED_STATUSES = {429, 500, 502, 503, 504}


class NotPublishedError(Exception):
    """The source does not have the field, or not yet."""


class Source(Protocol):
    """Where a model's fields are published."""

    def exists(self, run_time: datetime, hour: int, layer: str) -> bool:
        """Whether the source has a field.

        :param run_time: UTC start of the run
        :param hour: Hours since the run started
        :param layer: The field's variable, as the source names it
        :return: True if the field can be fetched
        """

    def fetch(self, run_time: datetime, hour: int, layer: str, path: Path):
        """Write a field to a file, as GRIB of one message.

        :param run_time: UTC start of the run
        :param hour: Hours since the run started
        :param layer: The field's variable, as the source names it
        :param path: The file to write
        :raises NotPublishedError: If the source does not have the field
        """


def _retrying(request):
    """Call `request`, retrying when the source is busy or the connection fails. A 404 raises
    NotPublishedError, and any other HTTP error is raised at once."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return request()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise NotPublishedError(error.url) from error
            if error.code not in RETRIED_STATUSES or attempt == ATTEMPTS:
                raise
        # Includes urllib.error.URLError, and timeouts.
        except (OSError, http.client.HTTPException):
            if attempt == ATTEMPTS:
                raise
        time.sleep(2 ** (attempt - 1) + random.uniform(0, 1))


def download(url: str, path: Path, byte_range: tuple[int, int | None] | None = None):
    """Write a URL's content to a file, retrying if the source is busy or the connection fails.

    :param url: The URL
    :param path: The file to write
    :param byte_range: The first and last bytes to write, or None for all of them. A last byte of
        None is the end
    :raises NotPublishedError: If it is not there
    :raises ValueError: If the source does not answer with the bytes asked for
    """

    def request():
        headers = {}
        if byte_range is not None:
            start, end = byte_range
            headers["Range"] = f"bytes={start}-{'' if end is None else end}"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=TIMEOUT_SECONDS
        ) as response:
            if byte_range is not None and response.status != 206:
                raise ValueError(f"{url} answered {response.status} to a byte range")
            with open(path, "wb") as out:
                shutil.copyfileobj(response, out)
            expected = response.headers.get("Content-Length")
        # A download that ends early is not an error to urllib.
        if expected is not None and path.stat().st_size != int(expected):
            raise ConnectionError(f"{url}: {path.stat().st_size} of {expected} bytes")

    _retrying(request)


def url_exists(url: str) -> bool:
    """Whether a URL is there, retrying if the source is busy or the connection fails.

    :param url: The URL
    :return: False if the source answers that it is not there
    """

    def request():
        head = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(head, timeout=TIMEOUT_SECONDS).close()

    try:
        _retrying(request)
        return True
    except NotPublishedError:
        return False


@lru_cache(maxsize=1024)
def read_text(url: str) -> str:
    """The text at a URL, read once: every variable of a forecast hour is in the same index.

    :param url: The URL
    :return: The text
    :raises NotPublishedError: If it is not there
    """

    def request():
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return response.read().decode()

    return _retrying(request)


@dataclass(frozen=True)
class MscDatamart:
    """The MSC datamart, which keeps about a day. A layer is as in its file names.

    :param model: The model, as in the file names
    :param folder: The model's folder
    :param grid: The model's grid, as in the file names
    """

    model: str
    folder: str
    grid: str

    def url(self, run_time: datetime, hour: int, layer: str) -> str:
        """A field's file.

        :param run_time: UTC start of the run
        :param hour: Hours since the run started
        :param layer: The field's variable, as in the file names
        :return: The file's URL
        """
        name = f"{run_time:%Y%m%dT%H}Z_MSC_{self.model}_{layer}_{self.grid}_PT{hour:03d}H.grib2"
        return f"https://dd.weather.gc.ca/today/{self.folder}/{run_time:%H}/{hour:03d}/{name}"

    def exists(self, run_time: datetime, hour: int, layer: str) -> bool:
        return url_exists(self.url(run_time, hour, layer))

    def fetch(self, run_time: datetime, hour: int, layer: str, path: Path):
        download(self.url(run_time, hour, layer), path)


class _IndexedSource:
    """A source with an index beside each GRIB file."""

    def urls(self, run_time: datetime, hour: int) -> tuple[str, str]:
        """A forecast hour's GRIB file, and its index.

        :param run_time: UTC start of the run
        :param hour: Hours since the run started
        :return: The URLs of the GRIB file and the index
        """
        raise NotImplementedError

    def find(self, index: str, layer: str) -> tuple[int, int | None] | None:
        """Find a field in an index.

        :param index: The index's text
        :param layer: The field's variable, as the source names it
        :return: The field's first and last bytes, or None if the index does not have it. A last
            byte of None is the end of the file
        """
        raise NotImplementedError

    def _byte_range(self, run_time: datetime, hour: int, layer: str) -> tuple[int, int | None]:
        index_url = self.urls(run_time, hour)[1]
        found = self.find(read_text(index_url), layer)
        if found is None:
            raise NotPublishedError(f"{layer} in {index_url}")
        return found

    def exists(self, run_time: datetime, hour: int, layer: str) -> bool:
        try:
            self._byte_range(run_time, hour, layer)
            return True
        except NotPublishedError:
            return False

    def fetch(self, run_time: datetime, hour: int, layer: str, path: Path):
        byte_range = self._byte_range(run_time, hour, layer)
        download(self.urls(run_time, hour)[0], path, byte_range)


class NoaaGfs(_IndexedSource):
    """NOAA's GFS 0.25 degree files on AWS, kept for years. NOMADS's filter would crop them, but
    it re-encodes the fields, which is not always exact.

    A layer is the start of a field's `variable:level:forecast` in the index.
    """

    def urls(self, run_time: datetime, hour: int) -> tuple[str, str]:
        url = (
            f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{run_time:%Y%m%d}/{run_time:%H}/atmos/"
            f"gfs.t{run_time:%H}z.pgrb2.0p25.f{hour:03d}"
        )
        return url, f"{url}.idx"

    def find(self, index: str, layer: str) -> tuple[int, int | None] | None:
        # number:offset:d=date:variable:level:forecast:
        lines = [line.split(":", 3) for line in index.splitlines()]
        found = None
        for position, (_, offset, _, field) in enumerate(lines):
            if field.startswith(layer):
                following = lines[position + 1 : position + 2]
                found = int(offset), int(following[0][1]) - 1 if following else None
        # The last one: hours 3 and 6 list the precipitation since the start twice.
        return found


class EcmwfOpenData(_IndexedSource):
    """ECMWF's IFS open data at 0.1 degree, on Google, which keeps it from October 2026.

    A layer is a parameter's short name.
    """

    def urls(self, run_time: datetime, hour: int) -> tuple[str, str]:
        url = (
            f"https://storage.googleapis.com/ecmwf-open-data/{run_time:%Y%m%d/%H}z/ifs/0p1/oper/"
            f"{run_time:%Y%m%d%H}0000-{hour}h-oper-fc-sfc"
        )
        return f"{url}.grib2", f"{url}.index"

    def find(self, index: str, layer: str) -> tuple[int, int | None] | None:
        for line in index.splitlines():
            field = json.loads(line)
            if field["param"] == layer and field["levtype"] == "sfc":
                return field["_offset"], field["_offset"] + field["_length"] - 1
        return None
