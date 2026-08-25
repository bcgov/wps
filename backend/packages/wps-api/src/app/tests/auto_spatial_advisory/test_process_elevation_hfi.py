from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

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


def _mock_process_hfi_elevation(mocker, exists: bool):
    """Patch process_hfi_elevation's dependencies and return its (process_tpi_by_firezone,
    store_elevation_tpi_stats) mocks. (await session.execute(stmt)).scalars().first() is
    synchronous once awaited, so it's stubbed with plain MagicMocks rather than the AsyncMock
    chain session auto-generates."""
    execute_result = MagicMock()
    execute_result.scalars.return_value.first.return_value = object() if exists else None

    mock_session = AsyncMock()
    mock_session.execute.return_value = execute_result

    mock_scope = mocker.patch(BASE + "get_async_write_session_scope")
    mock_scope.return_value.__aenter__.return_value = mock_session
    mocker.patch(BASE + "get_run_parameters_id", new_callable=AsyncMock)

    return (
        mocker.patch(BASE + "process_tpi_by_firezone", new_callable=AsyncMock),
        mocker.patch(BASE + "store_elevation_tpi_stats", new_callable=AsyncMock),
    )


@pytest.mark.anyio
async def test_process_hfi_elevation_computes_stats_when_missing(mocker):
    mock_process_tpi, mock_store = _mock_process_hfi_elevation(mocker, exists=False)

    await process_hfi_elevation(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mock_process_tpi.assert_awaited_once_with(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
    mock_store.assert_awaited_once()


@pytest.mark.anyio
async def test_process_hfi_elevation_skips_when_already_computed(mocker):
    mock_process_tpi, mock_store = _mock_process_hfi_elevation(mocker, exists=True)

    await process_hfi_elevation(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mock_process_tpi.assert_not_awaited()
    mock_store.assert_not_awaited()


@pytest.mark.anyio
async def test_store_elevation_tpi_stats_maps_tpi_classes_to_fields(mocker):
    fire_zone_tpi_stats = FireZoneTPIStats(
        fire_zone_stats={
            101: {1: 10, 2: 20, 3: 30},
            202: {1: 5},  # missing mid/upper slope classes
        },
        pixel_size_metres=90,
    )
    session = AsyncMock()
    mock_save = mocker.patch(BASE + "save_advisory_elevation_tpi_stats", new_callable=AsyncMock)

    await store_elevation_tpi_stats(
        session, run_parameters_id=5, fire_zone_tpi_stats=fire_zone_tpi_stats
    )

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
