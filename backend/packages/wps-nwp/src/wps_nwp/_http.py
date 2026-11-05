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
        self._concurrency = concurrency
        self._timeout = timeout
        self._retries = retries
        self._backoff = backoff
        self._session = session
        self._owns_session = session is None
        self._unreachable_until: dict[str, float] = {}

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def get(self, url: str, offset: int = 0, length: int | None = None) -> bytes:
        """Fetch a whole file, or length bytes from offset (to the end if length is None)."""
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
        try:
            await self._request("HEAD", url, {})
        except NotAvailable:
            return False
        return True

    async def _request(self, method: str, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
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
    try:
        return min(float(header), MAX_RETRY_AFTER_SECONDS)
    except (TypeError, ValueError):
        return 0.0
