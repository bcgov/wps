import asyncio
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.auto_spatial_advisory.nats_consumer import process_message
from app.auto_spatial_advisory.process_hfi import RunType


@pytest.mark.anyio
async def test_process_message_acks_after_success(monkeypatch):
    msg = Mock()
    msg.data = b'{"ignored": true}'
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()

    parse_message = Mock(
        return_value=(RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))
    )
    process_stats = AsyncMock()

    monkeypatch.setattr("app.auto_spatial_advisory.nats_consumer.parse_nats_message", parse_message)
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.process_sfms_hfi_stats", process_stats
    )

    await process_message(msg)

    parse_message.assert_called_once_with(msg)
    process_stats.assert_awaited_once_with(
        RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1)
    )
    msg.ack.assert_awaited_once()
    msg.nak.assert_not_called()


@pytest.mark.anyio
async def test_process_message_naks_after_failure(monkeypatch):
    msg = Mock()
    msg.data = b'{"ignored": true}'
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()

    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.parse_nats_message",
        Mock(return_value=(RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))),
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.process_sfms_hfi_stats",
        AsyncMock(side_effect=RuntimeError("boom")),
    )

    await process_message(msg)

    msg.ack.assert_not_called()
    msg.nak.assert_awaited_once()


@pytest.mark.anyio
async def test_keepalive_task_cancelled_on_success(monkeypatch):
    msg = Mock()
    msg.data = b'{"ignored": true}'
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()

    created_tasks = []
    real_create_task = asyncio.create_task

    def capturing_create_task(coro, **kwargs):
        task = real_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    monkeypatch.setattr("asyncio.create_task", capturing_create_task)
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.parse_nats_message",
        Mock(return_value=(RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))),
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.process_sfms_hfi_stats",
        AsyncMock(),
    )

    await process_message(msg)
    await asyncio.sleep(0)  # Let event loop process the cancellation

    assert len(created_tasks) == 1
    assert created_tasks[0].done()
    msg.ack.assert_awaited_once()


@pytest.mark.anyio
async def test_keepalive_task_cancelled_on_processing_failure(monkeypatch):
    msg = Mock()
    msg.data = b'{"ignored": true}'
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()

    created_tasks = []
    real_create_task = asyncio.create_task

    def capturing_create_task(coro, **kwargs):
        task = real_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    monkeypatch.setattr("asyncio.create_task", capturing_create_task)
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.parse_nats_message",
        Mock(return_value=(RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))),
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.process_sfms_hfi_stats",
        AsyncMock(side_effect=RuntimeError("processing failed")),
    )

    await process_message(msg)
    await asyncio.sleep(0)  # Let event loop process the cancellation

    assert len(created_tasks) == 1
    assert created_tasks[0].done()
    msg.nak.assert_awaited_once()


@pytest.mark.anyio
async def test_in_progress_sent_while_processing(monkeypatch):
    msg = Mock()
    msg.data = b'{"ignored": true}'
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()

    # Signal from in_progress back to slow_process so the test is deterministic
    in_progress_called = asyncio.Event()

    async def signal_in_progress():
        in_progress_called.set()

    msg.in_progress = AsyncMock(side_effect=signal_in_progress)

    # Patch sleep to yield without blocking so the keepalive fires immediately
    _real_sleep = asyncio.sleep
    monkeypatch.setattr("asyncio.sleep", lambda s: _real_sleep(0))

    async def slow_process(*args, **kwargs):
        # Block until keepalive has fired at least once, then allow processing to complete
        await in_progress_called.wait()

    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.parse_nats_message",
        Mock(return_value=(RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))),
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.nats_consumer.process_sfms_hfi_stats",
        slow_process,
    )

    await process_message(msg)

    msg.in_progress.assert_awaited()
