from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from aiohttp import ClientSession
from wps_wf1.wfwx_api import WfwxApi
from wps_wf1.wfwx_settings import WfwxSettings

from wps_shared import config
from wps_shared.utils.redis import create_redis


@dataclass
class _LifecycleFlags:
    owns_session: bool = False
    closed: bool = False


class WfwxService:
    """
    A service that creates and manages an WFWX API object. Supports async context management.
    - If a session is provided, it will be used and not closed by the service.
    - If no session is provided, the service creates and owns a ClientSession and closes it on exit.
    """

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        cache: Optional[object] = create_redis(),
    ):
        # We may create the session in __aenter__ if it's None.
        self.session: Optional[ClientSession] = session
        self._flags = _LifecycleFlags(owns_session=session is None)
        self.cache = cache

        # Defer WfwxApi construction until we have a session (in __aenter__)
        self.wfwx_api: Optional[WfwxApi] = None

        # Prebuild settings (pure data, safe to construct here)
        self._settings = WfwxSettings(
            base_url=config.get("WFWX_BASE_URL"),
            auth_url=config.get("WFWX_AUTH_URL"),
            user=config.get("WFWX_USER"),
            secret=config.get("WFWX_SECRET"),
            auth_cache_expiry=int(config.get("REDIS_AUTH_CACHE_EXPIRY", 600)),
        )

    async def __aenter__(self) -> "WfwxService":
        # Create a session if we own it and it doesn't exist yet
        if self.session is None:
            self.session = ClientSession()
            self._flags.owns_session = True

        # Construct the client now that we have a session
        self.wfwx_api = WfwxApi(
            session=self.session,
            settings=self._settings,
            cache=self.cache,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        """Idempotent close: closes owned session exactly once."""
        if self._flags.closed:
            return
        self._flags.closed = True

        # If we created the session, we close it here
        if self._flags.owns_session and self.session is not None:
            try:
                await self.session.close()
            finally:
                self.session = None
