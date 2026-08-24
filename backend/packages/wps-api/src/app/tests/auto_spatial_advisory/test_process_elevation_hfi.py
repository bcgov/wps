from contextlib import ExitStack
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auto_spatial_advisory.process_elevation_hfi import (
    FireZoneTPIStats,
    process_hfi_elevation,
    store_elevation_tpi_stats,
)
from app.auto_spatial_advisory.process_hfi import RunType

RUN_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
FOR_DATE = datetime(2025, 1, 1).date()
BASE = "app.auto_spatial_advisory.process_elevation_hfi."


@pytest.fixture
def mocks():
    """Patch process_hfi_elevation's dependencies, returning the mocked session's execute chain
    so tests can control whether stats already exist for this run."""
    with ExitStack() as stack:

        def patch_async(target: str) -> AsyncMock:
            return stack.enter_context(patch(BASE + target, new_callable=AsyncMock))

        mock_session = AsyncMock()
        mock_scope = stack.enter_context(patch(BASE + "get_async_write_session_scope"))
        mock_scope.return_value.__aenter__.return_value = mock_session

        yield {
            "session": mock_session,
            "get_run_parameters_id": patch_async("get_run_parameters_id"),
            "process_tpi_by_firezone": patch_async("process_tpi_by_firezone"),
            "store_elevation_tpi_stats": patch_async("store_elevation_tpi_stats"),
        }


def _set_existing_stats(mocks, exists: bool):
    """(await session.execute(stmt)).scalars().first() is synchronous once awaited, so it's
    stubbed with plain MagicMocks rather than the AsyncMock chain session auto-generates."""
    first_result = object() if exists else None
    scalars_result = MagicMock()
    scalars_result.first.return_value = first_result
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_result
    mocks["session"].execute.return_value = execute_result


@pytest.mark.anyio
async def test_process_hfi_elevation_computes_stats_when_missing(mocks):
    _set_existing_stats(mocks, exists=False)

    await process_hfi_elevation(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks["process_tpi_by_firezone"].assert_awaited_once_with(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
    mocks["store_elevation_tpi_stats"].assert_awaited_once()


@pytest.mark.anyio
async def test_process_hfi_elevation_skips_when_already_computed(mocks):
    _set_existing_stats(mocks, exists=True)

    await process_hfi_elevation(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks["process_tpi_by_firezone"].assert_not_awaited()
    mocks["store_elevation_tpi_stats"].assert_not_awaited()


@pytest.mark.anyio
async def test_store_elevation_tpi_stats_maps_tpi_classes_to_fields():
    fire_zone_tpi_stats = FireZoneTPIStats(
        fire_zone_stats={
            101: {1: 10, 2: 20, 3: 30},
            202: {1: 5},  # missing mid/upper slope classes
        },
        pixel_size_metres=90,
    )
    session = AsyncMock()

    with patch(BASE + "save_advisory_elevation_tpi_stats", new_callable=AsyncMock) as mock_save:
        await store_elevation_tpi_stats(session, run_parameters_id=5, fire_zone_tpi_stats=fire_zone_tpi_stats)

    mock_save.assert_awaited_once()
    saved_session, saved_list = mock_save.call_args.args
    assert saved_session is session
    assert len(saved_list) == 2

    complete_stat = next(s for s in saved_list if s.advisory_shape_id == 101)
    assert complete_stat.run_parameters == 5
    assert complete_stat.valley_bottom == 10
    assert complete_stat.mid_slope == 20
    assert complete_stat.upper_slope == 30
    assert complete_stat.pixel_size_metres == 90

    partial_stat = next(s for s in saved_list if s.advisory_shape_id == 202)
    assert partial_stat.valley_bottom == 5
    assert partial_stat.mid_slope == 0
    assert partial_stat.upper_slope == 0
