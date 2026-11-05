import asyncio
import logging
import random
import time
from urllib.parse import urlsplit

import aiohttp

from wps_nwp.errors import FetchError, NotAvailable

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
MAX_RETRY_AFTER_SECONDS = 60
# How long to stop sending requests to a host that could not be reached. Without this every
# queued request pays the full timeout and retry cost before falling back to another mirror.
HOST_COOLDOWN_SECONDS = 300


class Transport:
    """HTTP GETs with byte ranges, retries and a per-host circuit breaker."""

    def __init__(
        self,
        *,
        concurrency: int,
        timeout: float,
        retries: int,
        backoff: float,
        session: aiohttp.ClientSession | None,
    ):
        """
        Record the settings; nothing is opened.

        The session is created by the first request rather than here, for the reason given
        in _request. A session passed in is used as it is and is never closed by the
        transport. The arguments are those of Client.
        """
        self._concurrency = concurrency
        self._timeout = timeout
        self._retries = retries
        self._backoff = backoff
        self._session = session
        self._owns_session = session is None
        self._unreachable_until: dict[str, float] = {}

    async def close(self) -> None:
        """Close the session if this transport created it. One passed in is its owner's to close."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def get(self, url: str, offset: int = 0, length: int | None = None) -> bytes:
        """
        Fetch a whole file, or length bytes from offset (to the end if length is None).

        A Range header is sent unless the whole file is wanted. A server that honours it
        answers 206 with just those bytes. One that ignores it answers 200 with the whole
        file, and the range is cut out of that here. If a length was asked for and a different
        number of bytes came back, the response was cut short and FetchError is raised.
        Retries, missing files and other failures are dealt with by _request.

        :raises NotAvailable: the file does not exist
        :raises FetchError: the request failed, or returned the wrong number of bytes
        """
        headers = {}
        if offset or length is not None:
            last = "" if length is None else offset + length - 1
            headers["Range"] = f"bytes={offset}-{last}"
        status, body = await self._request("GET", url, headers)
        if headers and status != 206:
            # The server ignored the range and sent the whole file.
            body = body[offset : None if length is None else offset + length]
        if length is not None and len(body) != length:
            raise FetchError(url, f"expected {length} bytes but received {len(body)}")
        return body

    async def exists(self, url: str) -> bool:
        """
        Whether a URL exists, found out with a HEAD request so that no body is downloaded.

        True for a successful response and False for a 404. Any other failure raises
        FetchError after the usual retries, so that an outage is not read as absence.
        """
        try:
            await self._request("HEAD", url, {})
        except NotAvailable:
            return False
        return True

    async def _request(self, method: str, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        """
        Make one request, retrying failures that may be temporary.

        :return: the status and body of the first successful response

        - The session is created on first use, allowing at most concurrency connections to
          any one host; further requests to that host wait for a connection to come free. The
          timeout applies to connecting and to each wait for more data, not to the request as
          a whole, so a large file is not cut off while it is still arriving. Proxy settings
          are read from the environment.
        - A 404 raises NotAvailable at once. Any other status of 400 or above that is not in
          RETRYABLE_STATUSES raises FetchError at once, since asking again would get the same
          answer.
        - The statuses in RETRYABLE_STATUSES, timeouts and connection errors are retried, up
          to retries times. The wait before the first retry is backoff seconds and doubles
          each time, plus a random extra of up to backoff so that requests which failed
          together do not all retry together. If the server sent a Retry-After that is
          longer, that is used, up to MAX_RETRY_AFTER_SECONDS.
        - If the last attempt got no HTTP response at all, the host is marked unreachable for
          HOST_COOLDOWN_SECONDS. Until then every request to it fails immediately, including
          ones that were already waiting to retry, so that callers move on to another mirror.
        """
        if self._session is None:
            # Created here rather than in __init__ because it must be made inside the event loop.
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=0, limit_per_host=self._concurrency),
                timeout=aiohttp.ClientTimeout(
                    total=None, sock_connect=self._timeout, sock_read=self._timeout
                ),
                trust_env=True,
            )
        host = urlsplit(url).netloc
        for attempt in range(self._retries + 1):
            if self._unreachable_until.get(host, 0) > time.monotonic():
                raise FetchError(url, f"{host} is unreachable")
            delay = self._backoff * 2**attempt + random.uniform(0, self._backoff)
            status = None
            try:
                async with self._session.request(method, url, headers=headers) as response:
                    status = response.status
                    if status < 400:
                        return status, await response.read()
                    if status == 404:
                        raise NotAvailable(url)
                    if status not in RETRYABLE_STATUSES:
                        raise FetchError(url, f"HTTP {status}", status)
                    reason = f"HTTP {status}"
                    delay = max(delay, _retry_after(response.headers.get("Retry-After")))
            except (aiohttp.ClientError, TimeoutError) as error:
                reason = f"{type(error).__name__}: {error}".rstrip(": ")
            if attempt == self._retries:
                break
            logger.warning(
                "%s for %s; retry %d/%d in %.1fs", reason, url, attempt + 1, self._retries, delay
            )
            await asyncio.sleep(delay)

        if status is None:
            logger.warning(
                "%s is unreachable (%s); skipping it for %ds", host, reason, HOST_COOLDOWN_SECONDS
            )
            self._unreachable_until[host] = time.monotonic() + HOST_COOLDOWN_SECONDS
        raise FetchError(url, reason, status)


def _retry_after(header: str | None) -> float:
    """
    The seconds a Retry-After header asks for, capped at MAX_RETRY_AFTER_SECONDS.

    Only a number of seconds is understood. A missing header, or one giving a date, counts
    as zero, which leaves the usual backoff in charge.
    """
    try:
        return min(float(header), MAX_RETRY_AFTER_SECONDS)
    except (TypeError, ValueError):
        return 0.0
