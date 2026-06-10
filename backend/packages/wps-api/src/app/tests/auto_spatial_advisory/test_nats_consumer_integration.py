"""Integration tests for nats_consumer using a real NATS JetStream server.

These tests require Docker/Podman. Run with:
    cd backend && uv run pytest -m integration packages/wps-api/src/app/tests/auto_spatial_advisory/test_nats_consumer_integration.py
"""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock

import nats as nats_lib
import pytest
from testcontainers.nats import NatsContainer

from app.auto_spatial_advisory.nats_config import sfms_file_subject
from app.auto_spatial_advisory.nats_consumer import _setup_subscriber, process_message

_MODULE = "app.auto_spatial_advisory.nats_consumer"
_ACK_WAIT_TEST = 5  # seconds; production is 900
_KEEPALIVE_INTERVAL_TEST = 2  # seconds; production is 450


def _payload() -> bytes:
    inner = json.dumps(
        {
            "run_type": "actual",
            "for_date": "2025-01-01",
            "create_time": "2025-01-01T12:00:00",
        }
    )
    return json.dumps(inner).encode()


@pytest.fixture(scope="module")
def nats_uri():
    with NatsContainer(jetstream=True) as container:
        yield container.nats_uri()


@pytest.fixture
async def nats_setup(nats_uri, monkeypatch):
    test_id = uuid.uuid4().hex[:8]
    test_stream = f"test_sfms_{test_id}"
    test_durable = f"test_hfi_{test_id}"

    monkeypatch.setattr(f"{_MODULE}._ACK_WAIT", _ACK_WAIT_TEST)
    monkeypatch.setattr(f"{_MODULE}._KEEPALIVE_INTERVAL", _KEEPALIVE_INTERVAL_TEST)
    monkeypatch.setattr(f"{_MODULE}.stream_name", test_stream)
    monkeypatch.setattr(f"{_MODULE}.hfi_classify_durable_group", test_durable)

    nc = await nats_lib.connect(nats_uri)
    js = nc.jetstream()
    sub = await _setup_subscriber(js)

    yield js, sub, test_stream

    try:
        await js.delete_stream(test_stream)
    except Exception:
        pass
    await nc.close()


@pytest.mark.anyio
async def test_nats_redelivers_unacked_message(nats_setup):
    """Baseline: NATS redelivers a message when ack_wait expires without an ack."""
    js, sub, _ = nats_setup
    await js.publish(sfms_file_subject, _payload())

    [msg] = await sub.fetch(batch=1, timeout=5)
    assert msg.metadata.num_delivered == 1
    # Intentionally do not ack — let ack_wait expire.

    await asyncio.sleep(_ACK_WAIT_TEST + 1)

    [msg2] = await sub.fetch(batch=1, timeout=5)
    assert msg2.metadata.num_delivered == 2
    await msg2.ack()


@pytest.mark.anyio
async def test_message_acked_after_success(nats_setup, monkeypatch):
    """Successful processing calls ack (not nak), and the message is removed from the work queue."""
    js, sub, _ = nats_setup
    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", AsyncMock())
    await js.publish(sfms_file_subject, _payload())

    [msg] = await sub.fetch(batch=1, timeout=5)
    msg.ack = AsyncMock(wraps=msg.ack)
    msg.nak = AsyncMock(wraps=msg.nak)

    await process_message(msg)

    msg.ack.assert_awaited_once()
    msg.nak.assert_not_awaited()


@pytest.mark.anyio
async def test_keepalive_prevents_redelivery(nats_setup, monkeypatch):
    """Processing that exceeds ack_wait still acks successfully because keepalive extends the deadline."""
    js, sub, _ = nats_setup
    original_sleep = asyncio.sleep

    async def slow_process(*_):
        await original_sleep(_ACK_WAIT_TEST + 2)

    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", slow_process)
    await js.publish(sfms_file_subject, _payload())

    [msg] = await sub.fetch(batch=1, timeout=5)
    msg.ack = AsyncMock(wraps=msg.ack)
    msg.nak = AsyncMock(wraps=msg.nak)

    await process_message(msg)

    msg.ack.assert_awaited_once()
    msg.nak.assert_not_awaited()


@pytest.mark.anyio
async def test_message_nacked_after_failure(nats_setup, monkeypatch):
    """Processing failure naks the message; it remains in the stream for redelivery."""
    js, sub, _ = nats_setup
    monkeypatch.setattr(
        f"{_MODULE}.process_sfms_hfi_stats", AsyncMock(side_effect=RuntimeError("boom"))
    )
    await js.publish(sfms_file_subject, _payload())

    [msg] = await sub.fetch(batch=1, timeout=5)
    msg.ack = AsyncMock(wraps=msg.ack)
    msg.nak = AsyncMock(wraps=msg.nak)

    await process_message(msg)

    msg.nak.assert_awaited_once()
    msg.ack.assert_not_awaited()
