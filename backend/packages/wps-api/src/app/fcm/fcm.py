
import asyncio
from typing import List

from firebase_admin import messaging

from wps_shared.db.crud.fcm import deactivate_device_tokens
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fcm import DeviceToken
from wps_shared.utils.time import get_utc_now

# Simple exponential backoff with jitter for transient quota/server issues
async def _retry_send_multicast(multicast_msg: messaging.MulticastMessage,
                                max_retries: int = 5,
                                base_delay: float = 0.5):
    attempt = 0
    while True:
        try:
            return messaging.send_multicast(multicast_msg, dry_run=False)
        except Exception:
            # Retry on probable transient conditions: quota (429), backend unavailable, etc.
            # You can inspect e to match known transient cases in your logs.
            attempt += 1
            if attempt > max_retries:
                raise
            # Exponential backoff with jitter
            delay = (base_delay * (2 ** (attempt - 1))) + (0.1 * attempt)
            await asyncio.sleep(delay)


async def deactivate_bad_tokens(db, tokens: List[str], responses):
    """
    Deactivate tokens that failed with terminal errors like 'UNREGISTERED'.
    """
    # For MulticastResponse:
    # responses.responses[i].exception may contain details; many backends surface 'UNREGISTERED'
    # when a token is invalid/stale. Remove/deactivate those.
    stale_tokens: List[str] = []
    for idx, resp in enumerate(responses.responses):
        if not resp.success:
            exc = resp.exception
            if exc and hasattr(exc, "code"):
                code = getattr(exc, "code", None)
                # TODO: Potentially expand this list based on observed error codes.
                if str(code).upper() in {"UNREGISTERED"}:
                    stale_tokens.append(tokens[idx])
                    token = tokens[idx]
                    db.query(DeviceToken).filter(DeviceToken.token == token).update(
                        {"is_active": False, "updated_at": get_utc_now()}
                    )
    async with get_async_write_session_scope() as session:
        await deactivate_device_tokens(session, stale_tokens)
        
