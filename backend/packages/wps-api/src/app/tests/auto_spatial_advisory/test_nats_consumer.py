import asyncio
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.auto_spatial_advisory.nats_consumer import process_message
from app.auto_spatial_advisory.process_hfi import RunType

_MODULE = "app.auto_spatial_advisory.nats_consumer"
_PARSED_MSG = (RunType.ACTUAL, datetime(2025, 1, 1, 12, 0), date(2025, 1, 1))


@pytest.fixture
def msg():
    m = Mock()
    m.data = b'{"ignored": true}'
    m.ack = AsyncMock()
    m.nak = AsyncMock()
    return m


@pytest.fixture
def patch_parse(monkeypatch):
    mock = Mock(return_value=_PARSED_MSG)
    monkeypatch.setattr(f"{_MODULE}.parse_nats_message", mock)
    return mock


@pytest.fixture
def captured_tasks(monkeypatch):
    tasks = []
    real = asyncio.create_task

    def capture(coro, **kwargs):
        task = real(coro, **kwargs)
        tasks.append(task)
        return task

    monkeypatch.setattr("asyncio.create_task", capture)
    return tasks


@pytest.mark.anyio
async def test_process_message_acks_after_success(msg, patch_parse, monkeypatch):
    process_stats = AsyncMock()
    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", process_stats)

    await process_message(msg)

    patch_parse.assert_called_once_with(msg)
    process_stats.assert_awaited_once_with(*_PARSED_MSG)
    msg.ack.assert_awaited_once()
    msg.nak.assert_not_called()


@pytest.mark.anyio
async def test_process_message_naks_after_failure(msg, patch_parse, monkeypatch):
    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", AsyncMock(side_effect=RuntimeError("boom")))

    await process_message(msg)

    msg.ack.assert_not_called()
    msg.nak.assert_awaited_once()


@pytest.mark.anyio
async def test_keepalive_task_cancelled_on_success(msg, patch_parse, captured_tasks, monkeypatch):
    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", AsyncMock())

    await process_message(msg)
    await asyncio.sleep(0)

    assert len(captured_tasks) == 1
    assert captured_tasks[0].done()
    msg.ack.assert_awaited_once()


@pytest.mark.anyio
async def test_keepalive_task_cancelled_on_processing_failure(msg, patch_parse, captured_tasks, monkeypatch):
    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", AsyncMock(side_effect=RuntimeError("boom")))

    await process_message(msg)
    await asyncio.sleep(0)

    assert len(captured_tasks) == 1
    assert captured_tasks[0].done()
    msg.nak.assert_awaited_once()


@pytest.mark.anyio
async def test_in_progress_sent_while_processing(msg, patch_parse, monkeypatch):
    in_progress_called = asyncio.Event()

    async def signal_in_progress():
        in_progress_called.set()

    msg.in_progress = AsyncMock(side_effect=signal_in_progress)

    _real_sleep = asyncio.sleep
    monkeypatch.setattr("asyncio.sleep", lambda s: _real_sleep(0))

    async def slow_process(*args, **kwargs):
        await in_progress_called.wait()

    monkeypatch.setattr(f"{_MODULE}.process_sfms_hfi_stats", slow_process)

    await process_message(msg)

    msg.in_progress.assert_awaited()
