from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from wps_shared.run_type import RunType

from app.auto_spatial_advisory.local import process_stats_local


@pytest.mark.anyio
async def test_main_runs_shared_pipeline_with_fire_zone_validation(monkeypatch):
    session = AsyncMock()
    session_scope = MagicMock()
    session_scope.return_value.__aenter__.return_value = session
    run_datetime = datetime(2025, 1, 1, 12)
    get_run_parameters = AsyncMock(return_value=[SimpleNamespace(run_datetime=run_datetime)])
    process_stats = AsyncMock()
    monkeypatch.setattr(process_stats_local, "get_async_read_session_scope", session_scope)
    monkeypatch.setattr(process_stats_local, "get_most_recent_run_parameters", get_run_parameters)
    monkeypatch.setattr(process_stats_local, "process_sfms_hfi_stats", process_stats)

    for_date = date(2025, 1, 2)
    await process_stats_local.main([for_date], RunType.ACTUAL)

    process_stats.assert_awaited_once_with(RunType.ACTUAL, run_datetime, for_date)
