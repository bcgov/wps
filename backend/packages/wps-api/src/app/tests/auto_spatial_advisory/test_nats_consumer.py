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
